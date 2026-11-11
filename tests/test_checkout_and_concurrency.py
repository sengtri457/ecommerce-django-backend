from decimal import Decimal
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from apps.catalog.models import Category, Product, ProductVariant
from apps.orders.models import ShippingMethod, Order, OrderItem
from apps.orders.services import CheckoutService
from apps.inventory.models import StockMovement

class CheckoutAndConcurrencyTestCase(TestCase):
    def setUp(self):
        self.shipping_method = ShippingMethod.objects.create(
            code="phnom_penh_express",
            name="Phnom Penh Express",
            rate_usd=Decimal("2.50")
        )
        self.category = Category.objects.create(
            name="Clothes",
            slug="clothes",
            department="clothes"
        )
        self.product = Product.objects.create(
            title="Raw Denim Jacket",
            slug="raw-denim-jacket",
            description="Classic vintage washed jacket",
            category=self.category,
            base_price=Decimal("220.00")
        )
        self.variant_m = ProductVariant.objects.create(
            product=self.product,
            sku="CLO-0001-M",
            size="M",
            color="Washed Blue",
            stock=10
        )
        self.variant_s = ProductVariant.objects.create(
            product=self.product,
            sku="CLO-0001-S",
            size="S",
            color="Washed Blue",
            stock=2
        )

    def test_atomic_checkout_success(self):
        """Verify checkout decrements inventory atomically, writes audit log, and creates snapshots."""
        customer_data = {
            'name': 'Sophea Sok',
            'email': 'sophea@example.com',
            'phone': '012 345 678',
            'city_province': 'Phnom Penh',
            'khan_district': 'BKK',
            'street_address': 'Street 302, House 15',
            'shipping_method': 'phnom_penh_express',
            'payment_method': 'KHQR'
        }
        items_data = [
            {'variant_id': self.variant_m.id, 'quantity': 3}
        ]

        order, payment = CheckoutService.process_checkout(customer_data, items_data)

        # Reload variant from database
        self.variant_m.refresh_from_db()
        self.assertEqual(self.variant_m.stock, 7)  # 10 - 3 = 7

        # Check stock movement audit log
        movement = StockMovement.objects.filter(reference_id=order.order_number).first()
        self.assertIsNotNone(movement)
        self.assertEqual(movement.quantity_change, -3)
        self.assertEqual(movement.balance_after, 7)

        # Check order snapshot
        self.assertEqual(order.items.count(), 1)
        item = order.items.first()
        self.assertEqual(item.product_title, "Raw Denim Jacket")
        self.assertEqual(item.sku, "CLO-0001-M")
        self.assertEqual(item.size, "M")
        self.assertEqual(item.quantity, 3)
        self.assertEqual(item.unit_price, Decimal("220.00"))
        self.assertEqual(item.line_total, Decimal("660.00"))

        # Check complimentary shipping since total > $100
        self.assertEqual(order.shipping_cost, Decimal("0.00"))

        # Check payment record
        self.assertEqual(payment.payment_method, "KHQR")
        self.assertEqual(payment.amount_usd, order.total_usd)
        self.assertTrue(len(payment.khqr_payload) > 10)

    def test_insufficient_stock_rollback(self):
        """Verify requesting more stock than available aborts and rolls back stock deduction."""
        customer_data = {
            'name': 'Vireak Chan',
            'email': 'vireak@example.com',
            'phone': '098 765 432',
            'city_province': 'Siem Reap',
            'street_address': 'Wat Bo Road',
            'shipping_method': 'provincial',
            'payment_method': 'COD'
        }
        items_data = [
            {'variant_id': self.variant_s.id, 'quantity': 5}  # Only 2 in stock!
        ]

        with self.assertRaises(ValidationError) as ctx:
            CheckoutService.process_checkout(customer_data, items_data)

        self.assertIn("Insufficient inventory", str(ctx.exception))

        # Stock must remain unchanged
        self.variant_s.refresh_from_db()
        self.assertEqual(self.variant_s.stock, 2)
        self.assertEqual(Order.objects.count(), 0)

    def test_order_snapshot_isolation(self):
        """Verify that updating a product or variant does not alter previously completed orders."""
        customer_data = {
            'name': 'Dara Roth',
            'email': 'dara@example.com',
            'phone': '011 223 344',
            'city_province': 'Phnom Penh',
            'street_address': 'Street 51',
        }
        items_data = [{'variant_id': self.variant_m.id, 'quantity': 1}]

        order, _ = CheckoutService.process_checkout(customer_data, items_data)
        ordered_item = order.items.first()

        # Mutate the original product title and variant price
        self.product.title = "Altered Title 2027"
        self.product.base_price = Decimal("999.00")
        self.product.save()

        # Reload ordered item snapshot
        ordered_item.refresh_from_db()
        self.assertEqual(ordered_item.product_title, "Raw Denim Jacket")
        self.assertEqual(ordered_item.unit_price, Decimal("220.00"))
