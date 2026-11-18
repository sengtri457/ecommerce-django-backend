from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from apps.core.models import TimeStampedModel

class Category(TimeStampedModel):
    DEPARTMENT_CHOICES = (
        ('all', 'All Departments'),
        ('clothes', 'Clothes'),
        ('shoes', 'Shoes'),
        ('accessories', 'Accessories'),
    )
    AUDIENCE_CHOICES = (
        ('all', 'All Audiences'),
        ('men', 'Men'),
        ('women', 'Women'),
        ('kids', 'Kids'),
        ('unisex', 'Unisex'),
    )

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=150, unique=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    department = models.CharField(max_length=30, choices=DEPARTMENT_CHOICES, default='clothes')
    audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES, default='all')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['department', 'audience', 'is_active']),
        ]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} -> {self.name}"
        return self.name

class Product(TimeStampedModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField()
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products'
    )
    audience = models.CharField(max_length=20, default='all')
    department = models.CharField(max_length=50, default='all')
    subcategory = models.CharField(max_length=50, default='all')
    fabric = models.CharField(max_length=150, blank=True)
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['department', 'audience', 'is_active']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(base_price__gte=Decimal('0.00')),
                name='product_base_price_non_negative'
            )
        ]

    def __str__(self):
        return self.title

    @property
    def total_stock(self) -> int:
        return sum(v.stock for v in self.variants.filter(is_active=True))

    @property
    def primary_image(self):
        img = self.images.filter(is_primary=True).first()
        if not img:
            img = self.images.first()
        return img.image_url if img else ""

class ProductVariant(TimeStampedModel):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants'
    )
    sku = models.CharField(max_length=64, unique=True)
    size = models.CharField(max_length=30, blank=True)
    color = models.CharField(max_length=60, blank=True)
    color_hex = models.CharField(max_length=10, blank=True)
    price_override = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Product Variant'
        verbose_name_plural = 'Product Variants'
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['product', 'is_active']),
            models.Index(fields=['product', 'size']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'size', 'color'],
                name='unique_product_size_color'
            ),
            models.CheckConstraint(
                condition=models.Q(stock__gte=0),
                name='variant_stock_non_negative'
            ),
        ]

    def __str__(self):
        variant_desc = []
        if self.size:
            variant_desc.append(f"Size: {self.size}")
        if self.color:
            variant_desc.append(f"Color: {self.color}")
        details = f" ({', '.join(variant_desc)})" if variant_desc else ""
        return f"{self.product.title}{details} [{self.sku}]"

    @property
    def effective_price(self) -> Decimal:
        if self.price_override is not None:
            return self.price_override
        return self.product.base_price

class ProductImage(TimeStampedModel):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='images'
    )
    image_url = models.CharField(max_length=500)
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'
        ordering = ['sort_order', 'id']
        indexes = [
            models.Index(fields=['product', 'is_primary']),
        ]

    def __str__(self):
        return f"Image for {self.product.title} (Primary: {self.is_primary})"
