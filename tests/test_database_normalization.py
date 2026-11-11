from decimal import Decimal
from django.test import TestCase
from django.db import IntegrityError
from django.db.models import ProtectedError
from apps.catalog.models import Category, Product, ProductVariant, ProductImage
from apps.inventory.models import StockMovement

class DatabaseNormalizationTestCase(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Jackets",
            slug="jackets",
            department="clothes",
            audience="men"
        )
        self.product = Product.objects.create(
            title="Raw Denim Jacket",
            slug="raw-denim-jacket",
            description="Classic vintage washed jacket",
            category=self.category,
            base_price=Decimal("220.00"),
            audience="men",
            department="clothes",
            subcategory="sweater"
        )

    def test_product_variant_normalization(self):
        """Verify 3NF normalization: variants hold size, SKU, and inventory separately from product."""
        v_m = ProductVariant.objects.create(
            product=self.product,
            sku="CLO-0001-M",
            size="M",
            color="Washed Blue",
            stock=10
        )
        v_l = ProductVariant.objects.create(
            product=self.product,
            sku="CLO-0001-L",
            size="L",
            color="Washed Blue",
            stock=5
        )
        self.assertEqual(self.product.variants.count(), 2)
        self.assertEqual(self.product.total_stock, 15)
        self.assertEqual(v_m.effective_price, Decimal("220.00"))

    def test_unique_product_size_color_constraint(self):
        """Verify unique constraint prevents duplicate size-color variants under same product."""
        ProductVariant.objects.create(
            product=self.product,
            sku="CLO-0001-M",
            size="M",
            color="Washed Blue",
            stock=10
        )
        with self.assertRaises(IntegrityError):
            ProductVariant.objects.create(
                product=self.product,
                sku="CLO-0001-M-DUP",
                size="M",
                color="Washed Blue",
                stock=5
            )

    def test_stock_non_negative_constraint(self):
        """Verify database check constraint blocks negative inventory counts."""
        with self.assertRaises(IntegrityError):
            ProductVariant.objects.create(
                product=self.product,
                sku="CLO-0001-NEG",
                size="XL",
                color="Washed Blue",
                stock=-5
            )

    def test_category_protection_integrity(self):
        """Verify ON_DELETE=PROTECT prevents accidental deletion of categories containing products."""
        with self.assertRaises(ProtectedError):
            self.category.delete()

    def test_cascade_product_variants_and_images(self):
        """Verify deleting a product cascades to its associated variants and images."""
        variant = ProductVariant.objects.create(
            product=self.product,
            sku="CLO-0001-S",
            size="S",
            stock=5
        )
        image = ProductImage.objects.create(
            product=self.product,
            image_url="/collection/ctrl-blazer.webp",
            is_primary=True
        )
        self.product.delete()
        self.assertFalse(ProductVariant.objects.filter(id=variant.id).exists())
        self.assertFalse(ProductImage.objects.filter(id=image.id).exists())
