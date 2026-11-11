# Clothes™ & CTRL — Normalized Django Backend

Production-ready, 3NF/BCNF normalized eCommerce backend built with **Django 6.1** and **Django REST Framework (DRF)**.

---

## 1. Relational Database Normalization

The database architecture is designed with strict relational integrity:

- **1NF**: Atomic values for size, color, SKU, and image paths. No comma-separated fields.
- **2NF**: Attribute separation where base product metadata (`title`, `slug`, `category`, `base_price`) lives in `Product`, while concrete variations (`size`, `color`, `sku`, `stock`, `price_override`) live in `ProductVariant`.
- **3NF & Legal Invoicing Snapshots**: Non-transitive dependencies. Orders (`OrderItem`) capture point-in-time snapshots of purchased title, SKU, unit price, size, and color so future catalog edits never mutate past fiscal receipts.
- **Concurrency & Inventory Safety**:
  - `select_for_update()` row-level locks during checkout to eliminate overselling and race conditions.
  - Check constraints enforcing `stock >= 0` and `price >= 0`.
  - Unique composite constraint on `(product, size, color)`.
  - `StockMovement` immutable audit trail tracking all stock increments and decrements.

---

## 2. Domain Apps

| App | Purpose & Core Models |
| :--- | :--- |
| **`apps.catalog`** | `Category`, `Product`, `ProductVariant`, `ProductImage` |
| **`apps.inventory`** | `StockMovement` (PURCHASE, RESTOCK, RETURN, ADJUSTMENT) |
| **`apps.cart`** | `Cart`, `CartItem` (supports authenticated users and guest sessions) |
| **`apps.orders`** | `ShippingMethod`, `Order`, `OrderItem`, `OrderStatusHistory` |
| **`apps.payments`** | `Payment`, `PaymentTransaction` (Bakong KHQR, COD, Card) |
| **`apps.accounts`** | `User`, `CustomerAddress` (Cambodian location hierarchy) |

---

## 3. Quick Start

### Prerequisites
- Python 3.12+ (tested on Python 3.14.5)
- pip

### Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run migrations
python manage.py migrate

# 3. Seed catalog with realistic products and variants
python manage.py seed_catalog

# 4. Run automated test suite
python manage.py test tests

# 5. Start dev server
python manage.py runserver 8000
```

---

## 4. API Endpoints

- `GET /api/v1/catalog/categories/` — List all categories
- `GET /api/v1/catalog/products/` — List products with filters (`department`, `audience`, `category`, `subcategory`, `search`, `sort`)
- `GET /api/v1/catalog/products/<slug_or_id>/` — Retrieve product with variant matrix and stock
- `GET /api/v1/cart/` — Retrieve user/guest shopping cart
- `POST /api/v1/cart/items/` — Add variant to cart `{ "variant_id": 101, "quantity": 1 }`
- `PATCH /api/v1/cart/items/<id>/` — Modify quantity or selection status
- `DELETE /api/v1/cart/items/<id>/` — Remove item from cart
- `GET /api/v1/orders/shipping-methods/` — List Cambodian delivery methods & rates
- `POST /api/v1/orders/checkout/` — Atomic checkout with stock lock and KHQR generation
- `GET /api/v1/orders/<order_number>/` — Fetch order receipt & invoice
- `POST /api/v1/payments/<uuid:payment_id>/verify/` — Payment verification webhook
