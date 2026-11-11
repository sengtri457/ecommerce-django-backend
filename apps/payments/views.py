from decimal import Decimal
from django.utils import timezone
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from apps.payments.models import Payment, PaymentTransaction
from apps.payments.khqr import generate_khqr_payload, generate_khqr_md5

class PaymentStatusView(APIView):
    """
    Polling endpoint used by the frontend to check if customer has scanned and paid.
    """
    def get(self, request, payment_id):
        payment = get_object_or_404(Payment, id=payment_id)
        return Response({
            'payment_id': payment.id,
            'order_number': payment.order.order_number,
            'status': payment.status,
            'amount_usd': str(payment.amount_usd),
            'amount_khr': payment.amount_khr,
            'khqr_payload': payment.khqr_payload,
            'khqr_md5': payment.khqr_md5,
            'paid_at': payment.paid_at,
        }, status=status.HTTP_200_OK)

class PaymentVerifyView(APIView):
    """
    Webhook or verification endpoint for checking Bakong KHQR settlement.
    Can be invoked by bank webhook or admin verification.
    """
    def post(self, request, payment_id):
        payment = get_object_or_404(Payment, id=payment_id)

        # Mark payment as COMPLETED
        payment.status = 'COMPLETED'
        payment.paid_at = timezone.now()
        payment.save(update_fields=['status', 'paid_at'])

        # Update parent order status to CONFIRMED
        order = payment.order
        order.payment_status = 'PAID'
        order.status = 'CONFIRMED'
        order.save(update_fields=['payment_status', 'status'])

        PaymentTransaction.objects.create(
            payment=payment,
            action='VERIFIED_SUCCESSFUL',
            raw_data=request.data or {'status': 'PAID'}
        )

        return Response({
            'status': 'SUCCESS',
            'order_number': order.order_number,
            'payment_status': payment.status
        }, status=status.HTTP_200_OK)

class KHQRGenerateView(APIView):
    """
    Utility endpoint to dynamically generate EMVCo-compliant KHQR payload on the fly.
    """
    def post(self, request):
        amount = request.data.get('amount')
        currency = request.data.get('currency', 'USD').upper()
        bill_number = request.data.get('bill_number', 'TEST-BILL')

        if not amount:
            return Response({'error': 'Amount is required.'}, status=status.HTTP_400_BAD_REQUEST)

        bakong_account = getattr(settings, 'BAKONG_ACCOUNT_ID', 'clothes@abaa')
        merchant_name = getattr(settings, 'BAKONG_MERCHANT_NAME', 'Clothes Apparel Co')
        merchant_city = getattr(settings, 'BAKONG_MERCHANT_CITY', 'Phnom Penh')

        payload = generate_khqr_payload(
            bakong_account_id=bakong_account,
            merchant_name=merchant_name,
            merchant_city=merchant_city,
            amount=Decimal(str(amount)),
            currency=currency,
            bill_number=bill_number,
            store_label='Clothes'
        )
        md5_hash = generate_khqr_md5(payload)

        return Response({
            'qr_payload': payload,
            'md5': md5_hash,
            'bakong_account': bakong_account,
            'currency': currency,
            'amount': str(amount),
        }, status=status.HTTP_200_OK)
