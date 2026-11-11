from rest_framework import serializers
from apps.cart.models import Cart, CartItem
from apps.catalog.models import ProductVariant

class CartItemSerializer(serializers.ModelSerializer):
    variant_id = serializers.IntegerField(source='variant.id', read_only=True)
    product_id = serializers.IntegerField(source='variant.product.id', read_only=True)
    title = serializers.CharField(source='variant.product.title', read_only=True)
    sku = serializers.CharField(source='variant.sku', read_only=True)
    selected_size = serializers.CharField(source='variant.size', read_only=True)
    selected_color = serializers.CharField(source='variant.color', read_only=True)
    price = serializers.DecimalField(source='variant.effective_price', max_digits=10, decimal_places=2, read_only=True)
    thumbnail = serializers.CharField(source='variant.product.primary_image', read_only=True)
    max_stock = serializers.IntegerField(source='variant.stock', read_only=True)
    line_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = [
            'id',
            'variant_id',
            'product_id',
            'title',
            'sku',
            'selected_size',
            'selected_color',
            'price',
            'thumbnail',
            'quantity',
            'max_stock',
            'is_selected',
            'line_total',
        ]

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    item_count = serializers.IntegerField(source='total_items', read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = [
            'id',
            'items',
            'item_count',
            'subtotal',
            'updated_at',
        ]

class AddToCartSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField()
    quantity = serializers.IntegerField(default=1, min_value=1)

    def validate_variant_id(self, value):
        try:
            variant = ProductVariant.objects.get(id=value, is_active=True)
        except ProductVariant.DoesNotExist:
            raise serializers.ValidationError("Product variant does not exist or is inactive.")
        if variant.stock < 1:
            raise serializers.ValidationError(f"Variant '{variant.sku}' is currently out of stock.")
        return value
