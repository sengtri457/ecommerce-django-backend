"""
URL configuration for ecommerce-django-backend.
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.catalog.views import CategoryListView, ProductViewSet
from apps.cart.views import CartDetailView, CartItemAddView, CartItemDetailView
from apps.orders.views import (
    ShippingMethodListView,
    CheckoutView,
    OrderDetailView,
)
from apps.payments.views import (
    PaymentStatusView,
    PaymentVerifyView,
    KHQRGenerateView,
)

router = DefaultRouter()
router.register(r'catalog/products', ProductViewSet, basename='products')

urlpatterns = [
    path('admin/', admin.site.urls),

    # Catalog
    path('api/v1/catalog/categories/', CategoryListView.as_view(), name='category-list'),
    path('api/v1/', include(router.urls)),

    # Cart
    path('api/v1/cart/', CartDetailView.as_view(), name='cart-detail'),
    path('api/v1/cart/items/', CartItemAddView.as_view(), name='cart-item-add'),
    path('api/v1/cart/items/<int:item_id>/', CartItemDetailView.as_view(), name='cart-item-detail'),

    # Orders & Checkout
    path('api/v1/orders/shipping-methods/', ShippingMethodListView.as_view(), name='shipping-methods'),
    path('api/v1/orders/checkout/', CheckoutView.as_view(), name='order-checkout'),
    path('api/v1/orders/<str:order_number>/', OrderDetailView.as_view(), name='order-detail'),

    # Payments & Bakong KHQR
    path('api/v1/payments/<uuid:payment_id>/status/', PaymentStatusView.as_view(), name='payment-status'),
    path('api/v1/payments/<uuid:payment_id>/verify/', PaymentVerifyView.as_view(), name='payment-verify'),
    path('api/v1/payments/khqr/generate/', KHQRGenerateView.as_view(), name='khqr-generate'),
]
