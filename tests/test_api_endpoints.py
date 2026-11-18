from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.catalog.models import Category, Product, ProductVariant
from apps.orders.models import ShippingMethod

class ApiEndpointsTestCase(APITestCase):
    def setUp(self):
        self.shipping_method = ShippingMethod.objects.create(
            code="phnom_penh_express",
            name="Phnom Penh Express",
            rate_usd=Decimal("2.50")
        )
        self.category = Category.objects.create(
            name="Clothes",
            slug="clothes",
            department="clothes",
            audience="men"
        )
        self.product = Product.objects.create(
            title="Raw Denim Jacket",
            slug="raw-denim-jacket",
            description="Classic vintage washed jacket",
            category=self.category,
            base_price=Decimal("220.00"),
            audience="men",
            department="clothes",
            subcategory="sweater"
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            sku="CLO-0001-M",
            size="M",
            color="Washed Blue",
            stock=15
        )

    def test_list_products_endpoint(self):
        url = reverse('products-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['slug'], 'raw-denim-jacket')

    def test_retrieve_product_detail_endpoint(self):
        url = reverse('products-detail', kwargs={'slug': 'raw-denim-jacket'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Raw Denim Jacket')
        self.assertEqual(len(response.data['variants']), 1)
        self.assertEqual(response.data['variants'][0]['sku'], 'CLO-0001-M')
        self.assertEqual(response.data['variants'][0]['stock'], 15)

    def test_cart_add_and_get_endpoint(self):
        add_url = reverse('cart-item-add')
        payload = {'variant_id': self.variant.id, 'quantity': 2}
        response = self.client.post(add_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['item_count'], 2)
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['items'][0]['selected_size'], 'M')

    def test_checkout_endpoint(self):
        checkout_url = reverse('order-checkout')
        payload = {
            'name': 'Bopha Pich',
            'email': 'bopha@example.com',
            'phone': '077 112 233',
            'city_province': 'Phnom Penh',
            'khan_district': 'Chamkarmon',
            'street_address': 'Street 271, House 4B',
            'shipping_method': 'phnom_penh_express',
            'payment_method': 'KHQR',
            'items': [
                {'variant_id': self.variant.id, 'quantity': 1}
            ]
        }
        response = self.client.post(checkout_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('order', response.data)
        self.assertIn('payment', response.data)
        self.assertEqual(response.data['order']['customer_name'], 'Bopha Pich')
        self.assertEqual(response.data['payment']['method'], 'KHQR')
