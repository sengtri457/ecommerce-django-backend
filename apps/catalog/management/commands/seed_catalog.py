import os
import json
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.catalog.models import Category, Product, ProductVariant, ProductImage
from apps.inventory.models import StockMovement
from apps.orders.models import ShippingMethod

class Command(BaseCommand):
    help = 'Seeds database with categories, shipping methods, products, and normalized variants.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("--- Starting Database Seeding ---")

        # 1. Seed Shipping Methods for Cambodia
        shipping_methods = [
            {
                'code': 'phnom_penh_express',
                'name': 'Phnom Penh Express (Same-Day Rider)',
                'rate_usd': Decimal('2.50'),
                'estimated_delivery_days': '2-4 hours',
            },
            {
                'code': 'phnom_penh_standard',
                'name': 'Phnom Penh Standard (Next Day Delivery - Free)',
                'rate_usd': Decimal('0.00'),
                'estimated_delivery_days': '24 hours',
            },
            {
                'code': 'provincial',
                'name': 'Cambodia Provincial Delivery (Virak Buntham / J&T)',
                'rate_usd': Decimal('3.00'),
                'estimated_delivery_days': '1-3 business days',
            },
        ]

        for sm_data in shipping_methods:
            sm, created = ShippingMethod.objects.update_or_create(
                code=sm_data['code'],
                defaults=sm_data
            )
            status = "Created" if created else "Updated"
            self.stdout.write(f"ShippingMethod: {sm.name} [{status}]")

        # 2. Seed Root & Sub Categories
        root_categories = {
            'Clothes': Category.objects.get_or_create(
                slug='clothes',
                defaults={'name': 'Clothes', 'department': 'clothes', 'sort_order': 1}
            )[0],
            'Shoes': Category.objects.get_or_create(
                slug='shoes',
                defaults={'name': 'Shoes', 'department': 'shoes', 'sort_order': 2}
            )[0],
            'Accessories': Category.objects.get_or_create(
                slug='accessories',
                defaults={'name': 'Accessories', 'department': 'accessories', 'sort_order': 3}
            )[0],
        }

        # 3. Load Seed Data from JSON
        json_path = os.path.join(os.path.dirname(__file__), 'seed_data.json')
        if not os.path.exists(json_path):
            self.stderr.write(f"Error: {json_path} does not exist.")
            return

        with open(json_path, 'r', encoding='utf-8') as f:
            items = json.load(f)

        products_created = 0
        variants_created = 0

        for item in items:
            cat_name = item.get('category', 'Clothes')
            parent_cat = root_categories.get(cat_name, root_categories['Clothes'])

            subcat_slug = f"{item['department']}-{item['subcategory']}".lower()
            category, _ = Category.objects.get_or_create(
                slug=subcat_slug,
                defaults={
                    'name': item['subcategory'].replace('_', ' ').capitalize(),
                    'parent': parent_cat,
                    'department': item['department'],
                    'audience': item['audience'],
                }
            )

            product, p_created = Product.objects.update_or_create(
                slug=item['slug'],
                defaults={
                    'title': item['title'],
                    'description': item['description'],
                    'category': category,
                    'audience': item['audience'],
                    'department': item['department'],
                    'subcategory': item['subcategory'],
                    'fabric': item.get('fabric', ''),
                    'base_price': Decimal(str(item['price'])),
                    'is_active': True,
                    'is_featured': True if products_created < 4 else False,
                }
            )
            if p_created:
                products_created += 1

            # Seed primary image
            ProductImage.objects.get_or_create(
                product=product,
                image_url=item['thumbnail'],
                defaults={
                    'alt_text': item['title'],
                    'is_primary': True,
                    'sort_order': 0,
                }
            )

            # Seed variants for each size
            sizes = item.get('sizes') or ['Standard']
            total_stock = item.get('stock', 20)
            stock_per_size = max(1, total_stock // len(sizes))

            for idx, size in enumerate(sizes):
                # Distribute stock across sizes, with one size potentially having low stock for testing
                if idx == len(sizes) - 1:
                    size_stock = max(0, total_stock - (stock_per_size * (len(sizes) - 1)))
                else:
                    size_stock = stock_per_size

                clean_size = size.upper().replace(' ', '')
                sku = f"CLO-{item['id']:04d}-{clean_size}"

                variant, v_created = ProductVariant.objects.update_or_create(
                    product=product,
                    size=size,
                    color=item.get('fabric', '').split('&')[0].strip() if item.get('fabric') else '',
                    defaults={
                        'sku': sku,
                        'price_override': None,
                        'stock': size_stock,
                        'is_active': True,
                        'is_default': (idx == 0),
                    }
                )
                if v_created:
                    variants_created += 1
                    # Record initial stock balance movement
                    StockMovement.objects.create(
                        variant=variant,
                        quantity_change=size_stock,
                        movement_type='RESTOCK',
                        balance_after=size_stock,
                        notes='Initial catalog inventory seed'
                    )

        self.stdout.write(self.style.SUCCESS(
            f"Successfully seeded {products_created} products, {variants_created} variants, and stock records!"
        ))
