from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.payments.khqr import generate_khqr_payload, generate_khqr_md5, crc16_ccitt
from apps.payments.models import Payment
from apps.orders.models import Order, ShippingMethod

class KHQRPaymentTestCase(APITestCase):
    def setUp(self):
        self.shipping_method = ShippingMethod.objects.create(
            code="phnom_penh_express",
            name="Phnom Penh Express",
            rate_usd=Decimal("2.50")
        )
        self.order = Order.objects.create(
            order_number="CLO-20261111-TEST01",
            customer_name="Sok Chan",
            customer_email="sok@example.com",
            customer_phone="012999888",
            city_province="Phnom Penh",
            street_address="Street 240, No 10",
            shipping_method=self.shipping_method,
            subtotal=Decimal("220.00"),
            tax=Decimal("22.00"),
            shipping_cost=Decimal("0.00"),
            total_usd=Decimal("242.00"),
            total_khr=992200
        )
        self.payment = Payment.objects.create(
            order=self.order,
            payment_method="KHQR",
            amount_usd=Decimal("242.00"),
            amount_khr=992200,
            status="PENDING"
        )

    def test_emvco_khqr_payload_generation(self):
        payload = generate_khqr_payload(
            bakong_account_id="clothes@abaa",
            merchant_name="Clothes Apparel Co",
            merchant_city="Phnom Penh",
            amount=Decimal("242.00"),
            currency="USD",
            bill_number=self.order.order_number
        )
        # Check standard EMVCo root tags
        self.assertTrue(payload.startswith("000201010212"))  # Tag 00 (01) & Tag 01 (12 dynamic)
        self.assertIn("5802KH", payload)                    # Country code KH
        self.assertIn("5303840", payload)                   # Currency USD (840)
        self.assertTrue("242" in payload)                    # Amount
        self.assertIn("CLO-20261111-TEST01", payload)       # Bill Number

        # Check valid CRC16 Tag 63 at end
        self.assertIn("6304", payload)
        expected_crc = crc16_ccitt(payload[:-4])
        self.assertEqual(payload[-4:], expected_crc)

    def test_payment_status_polling_endpoint(self):
        url = reverse('payment-status', kwargs={'payment_id': self.payment.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'PENDING')
        self.assertEqual(response.data['order_number'], self.order.order_number)

    def test_payment_verify_webhook_endpoint(self):
        url = reverse('payment-verify', kwargs={'payment_id': self.payment.id})
        response = self.client.post(url, {'status': 'COMPLETED'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Reload from db
        self.payment.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(self.payment.status, 'COMPLETED')
        self.assertIsNotNone(self.payment.paid_at)
        self.assertEqual(self.order.payment_status, 'PAID')
        self.assertEqual(self.order.status, 'CONFIRMED')
