from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.orders.models import Order, ShippingMethod
from apps.orders.serializers import (
    OrderSerializer,
    ShippingMethodSerializer,
    CheckoutInputSerializer,
)
from apps.orders.services import CheckoutService
from apps.cart.views import get_or_create_cart

class ShippingMethodListView(generics.ListAPIView):
    queryset = ShippingMethod.objects.filter(is_active=True)
    serializer_class = ShippingMethodSerializer
    pagination_class = None

class CheckoutView(APIView):
    def post(self, request):
        serializer = CheckoutInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer_data = serializer.validated_data

        cart = None
        items_data = customer_data.get('items')

        # If items not passed directly, pull from user or guest cart
        if not items_data:
            cart = get_or_create_cart(request)
            selected_items = cart.items.filter(is_selected=True)
            if not selected_items.exists():
                return Response(
                    {"detail": "No selected items in bag to checkout."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            items_data = [
                {'variant_id': ci.variant.id, 'quantity': ci.quantity}
                for ci in selected_items
            ]

        order, payment = CheckoutService.process_checkout(
            customer_data=customer_data,
            items_data=items_data,
            user=request.user,
            cart=cart
        )

        response_data = {
            'order': OrderSerializer(order).data,
            'payment': {
                'id': payment.id,
                'method': payment.payment_method,
                'status': payment.status,
                'amount_usd': str(payment.amount_usd),
                'amount_khr': payment.amount_khr,
                'khqr_payload': payment.khqr_payload,
                'khqr_md5': payment.khqr_md5,
            }
        }
        return Response(response_data, status=status.HTTP_201_CREATED)

class OrderDetailView(generics.RetrieveAPIView):
    queryset = Order.objects.all().prefetch_related('items')
    serializer_class = OrderSerializer
    lookup_field = 'order_number'
