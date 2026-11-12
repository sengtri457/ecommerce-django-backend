import uuid
import datetime
from decimal import Decimal
from django.db import transaction
from django.conf import settings
from rest_framework.exceptions import ValidationError
from apps.catalog.models import ProductVariant
from apps.inventory.models import StockMovement
from apps.orders.models import Order, OrderItem, ShippingMethod
from apps.payments.models import Payment, PaymentTransaction
from apps.payments.khqr import generate_khqr_payload, generate_khqr_md5

class CheckoutService:
    @classmethod
    @transaction.atomic
    def process_checkout(cls, customer_data: dict, items_data: list, user=None, cart=None) -> tuple[Order, Payment]:
        if not items_data:
            raise ValidationError("Cannot checkout with an empty cart.")

        # 1. Fetch Shipping Method
        shipping_code = customer_data.get('shipping_method', 'phnom_penh_express')
        try:
            shipping_method = ShippingMethod.objects.get(code=shipping_code, is_active=True)
        except ShippingMethod.DoesNotExist:
            shipping_method = ShippingMethod.objects.first()

        # 2. Acquire database row-level lock on variants (Concurrency safe against overselling)
        variant_ids = [item['variant_id'] for item in items_data]
        locked_variants = {
            v.id: v
            for v in ProductVariant.objects.select_for_update().filter(id__in=variant_ids)
        }

        # 3. Validate availability & stock
        for item in items_data:
            v_id = item['variant_id']
            qty = item['quantity']
            variant = locked_variants.get(v_id)

            if not variant or not variant.is_active:
                raise ValidationError(f"Item with variant ID {v_id} is no longer available.")

            if variant.stock < qty:
                raise ValidationError(
                    f"Insufficient inventory for '{variant.product.title}' (Size: {variant.size}). "
                    f"Requested {qty}, but only {variant.stock} left in stock."
                )

        # 4. Calculate Subtotal
        subtotal = Decimal('0.00')
        order_items_to_create = []

        for item in items_data:
            variant = locked_variants[item['variant_id']]
            qty = item['quantity']
            unit_price = variant.effective_price
            line_total = unit_price * qty
            subtotal += line_total

            order_items_to_create.append({
                'variant': variant,
                'product_title': variant.product.title,
                'sku': variant.sku,
                'size': variant.size,
                'color': variant.color,
                'unit_price': unit_price,
                'quantity': qty,
                'line_total': line_total,
            })

        # Phnom Penh Standard is Free; or complimentary shipping threshold ($100 USD)
        if shipping_method.code == 'phnom_penh_standard' or subtotal >= Decimal('100.00'):
            shipping_cost = Decimal('0.00')
        else:
            shipping_cost = shipping_method.rate_usd

        tax_rate = getattr(settings, 'DEFAULT_TAX_RATE', Decimal('0.10'))
        tax = (subtotal * tax_rate).quantize(Decimal('0.01'))
        total_usd = subtotal + shipping_cost + tax

        # Generate unique order number
        today_str = datetime.date.today().strftime('%Y%m%d')
        random_suffix = uuid.uuid4().hex[:6].upper()
        order_number = f"CLO-{today_str}-{random_suffix}"

        # 5. Create Order
        order = Order.objects.create(
            order_number=order_number,
            user=user if user and user.is_authenticated else None,
            customer_name=customer_data['name'],
            customer_email=customer_data['email'],
            customer_phone=customer_data['phone'],
            customer_telegram=customer_data.get('telegram', ''),
            city_province=customer_data.get('city_province', 'Phnom Penh'),
            khan_district=customer_data.get('khan_district', ''),
            sangkat_commune=customer_data.get('sangkat_commune', ''),
            street_address=customer_data.get('street_address', ''),
            landmark=customer_data.get('landmark', ''),
            shipping_method=shipping_method,
            shipping_cost=shipping_cost,
            subtotal=subtotal,
            tax=tax,
            total_usd=total_usd,
            status='PENDING',
            payment_status='UNPAID',
            order_notes=customer_data.get('order_notes', '')
        )

        # 6. Deduct stock atomically and log inventory movement
        for item_data in order_items_to_create:
            variant = item_data['variant']
            qty = item_data['quantity']

            variant.stock -= qty
            variant.save(update_fields=['stock'])

            StockMovement.objects.create(
                variant=variant,
                quantity_change=-qty,
                movement_type='PURCHASE',
                reference_id=order.order_number,
                balance_after=variant.stock,
                notes=f"Order {order.order_number} checkout"
            )

            OrderItem.objects.create(
                order=order,
                variant=variant,
                product_title=item_data['product_title'],
                sku=item_data['sku'],
                size=item_data['size'],
                color=item_data['color'],
                unit_price=item_data['unit_price'],
                quantity=qty,
                line_total=item_data['line_total']
            )

        # 7. Create Payment record
        payment_method = customer_data.get('payment_method', 'KHQR').upper()
        payment = Payment.objects.create(
            order=order,
            payment_method=payment_method,
            amount_usd=total_usd,
            amount_khr=order.total_khr,
            status='PENDING'
        )

        if payment_method == 'KHQR':
            bakong_account = getattr(settings, 'BAKONG_ACCOUNT_ID', 'clothes@abaa')
            merchant_name = getattr(settings, 'BAKONG_MERCHANT_NAME', 'Clothes Apparel Co')
            merchant_city = getattr(settings, 'BAKONG_MERCHANT_CITY', 'Phnom Penh')
            phone_number = getattr(settings, 'BAKONG_PHONE_NUMBER', '')

            # Generate EMVCo compliant Dynamic KHQR payload using loaded merchant credentials
            payload = generate_khqr_payload(
                bakong_account_id=bakong_account,
                merchant_name=merchant_name,
                merchant_city=merchant_city,
                amount=total_usd,
                currency='USD',
                bill_number=order.order_number,
                store_label=merchant_name,
                phone_number=phone_number,
            )
            md5_hash = generate_khqr_md5(payload)

            payment.khqr_payload = payload
            payment.khqr_md5 = md5_hash
            payment.transaction_reference = md5_hash
            payment.save(update_fields=['khqr_payload', 'khqr_md5', 'transaction_reference'])

            PaymentTransaction.objects.create(
                payment=payment,
                action='KHQR_GENERATED',
                raw_data={'khqr_md5': md5_hash, 'amount_usd': str(total_usd)}
            )

        # 8. Clear purchased items from cart if cart provided
        if cart:
            cart.items.filter(variant_id__in=variant_ids).delete()

        return order, payment
