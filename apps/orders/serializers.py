from rest_framework import serializers
from apps.orders.models import Order, OrderItem, ShippingMethod
from apps.payments.models import Payment

class ShippingMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingMethod
        fields = ['id', 'code', 'name', 'rate_usd', 'estimated_delivery_days']

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            'id',
            'product_title',
            'sku',
            'size',
            'color',
            'unit_price',
            'quantity',
            'line_total',
        ]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    shipping_method = ShippingMethodSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'order_number',
            'customer_name',
            'customer_email',
            'customer_phone',
            'customer_telegram',
            'city_province',
            'khan_district',
            'sangkat_commune',
            'street_address',
            'landmark',
            'shipping_method',
            'shipping_cost',
            'subtotal',
            'tax',
            'total_usd',
            'total_khr',
            'status',
            'payment_status',
            'tracking_number',
            'order_notes',
            'items',
            'created_at',
        ]

class CheckoutItemInputSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

class CheckoutInputSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=32)
    telegram = serializers.CharField(max_length=64, required=False, allow_blank=True)
    city_province = serializers.CharField(max_length=100)
    khan_district = serializers.CharField(max_length=100, required=False, allow_blank=True)
    sangkat_commune = serializers.CharField(max_length=100, required=False, allow_blank=True)
    street_address = serializers.CharField(max_length=255)
    landmark = serializers.CharField(max_length=255, required=False, allow_blank=True)
    shipping_method = serializers.CharField(max_length=40, default='phnom_penh_express')
    payment_method = serializers.CharField(max_length=20, default='KHQR')
    order_notes = serializers.CharField(required=False, allow_blank=True)

    items = CheckoutItemInputSerializer(many=True, required=False)
