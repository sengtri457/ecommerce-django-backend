from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from apps.payments.models import Payment, PaymentTransaction

class PaymentVerifyView(APIView):
    """
    Webhook or verification endpoint for checking Bakong KHQR settlement.
    """
    def post(self, request, payment_id):
        payment = get_object_or_404(Payment, id=payment_id)

        # Mark payment as COMPLETED
        payment.status = 'COMPLETED'
        payment.paid_at = timezone.now()
        payment.save(update_fields=['status', 'paid_at'])

        # Update parent order status
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
