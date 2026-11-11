from rest_framework import serializers
from apps.catalog.models import Category, Product, ProductVariant, ProductImage

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'parent', 'department', 'audience', 'description']

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image_url', 'alt_text', 'is_primary', 'sort_order']

class ProductVariantSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(source='effective_price', max_digits=10, decimal_places=2)

    class Meta:
        model = ProductVariant
        fields = [
            'id',
            'sku',
            'size',
            'color',
            'color_hex',
            'price',
            'stock',
            'is_default',
            'is_active',
        ]

class ProductListSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(source='base_price', max_digits=10, decimal_places=2)
    thumbnail = serializers.CharField(source='primary_image', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    total_stock = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'slug',
            'title',
            'price',
            'thumbnail',
            'category_name',
            'department',
            'audience',
            'subcategory',
            'total_stock',
            'is_featured',
        ]

class ProductDetailSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(source='base_price', max_digits=10, decimal_places=2)
    thumbnail = serializers.CharField(source='primary_image', read_only=True)
    category = CategorySerializer(read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    total_stock = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'slug',
            'title',
            'description',
            'price',
            'thumbnail',
            'category',
            'department',
            'audience',
            'subcategory',
            'fabric',
            'variants',
            'images',
            'total_stock',
            'is_featured',
        ]
