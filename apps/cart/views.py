import uuid
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from apps.cart.models import Cart, CartItem
from apps.catalog.models import ProductVariant
from apps.cart.serializers import CartSerializer, CartItemSerializer, AddToCartSerializer

def get_or_create_cart(request) -> Cart:
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user, is_active=True)
        return cart

    session_id = request.headers.get('X-Session-ID') or request.session.session_key
    if not session_id:
        if not request.session.exists(request.session.session_key):
            request.session.create()
        session_id = request.session.session_key or str(uuid.uuid4())

    cart, _ = Cart.objects.get_or_create(session_key=session_id, is_active=True)
    return cart

class CartDetailView(APIView):
    def get(self, request):
        cart = get_or_create_cart(request)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

class CartItemAddView(APIView):
    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart = get_or_create_cart(request)
        variant = ProductVariant.objects.get(id=serializer.validated_data['variant_id'])
        quantity = serializer.validated_data['quantity']

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            variant=variant,
            defaults={'quantity': quantity, 'is_selected': True}
        )

        if not created:
            # Check maximum stock
            new_qty = cart_item.quantity + quantity
            if new_qty > variant.stock:
                new_qty = variant.stock
            cart_item.quantity = new_qty
            cart_item.is_selected = True
            cart_item.save(update_fields=['quantity', 'is_selected'])

        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)

class CartItemDetailView(APIView):
    def patch(self, request, item_id):
        cart = get_or_create_cart(request)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)

        quantity = request.data.get('quantity')
        is_selected = request.data.get('is_selected')

        if quantity is not None:
            qty = int(quantity)
            if qty <= 0:
                cart_item.delete()
                return Response(CartSerializer(cart).data)
            cart_item.quantity = min(qty, cart_item.variant.stock)

        if is_selected is not None:
            cart_item.is_selected = bool(is_selected)

        cart_item.save()
        return Response(CartSerializer(cart).data)

    def delete(self, request, item_id):
        cart = get_or_create_cart(request)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        cart_item.delete()
        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)
