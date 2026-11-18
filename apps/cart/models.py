from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from apps.core.models import TimeStampedModel, UUIDModel
from apps.catalog.models import ProductVariant

class Cart(TimeStampedModel, UUIDModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='carts'
    )
    session_key = models.CharField(max_length=120, blank=True, db_index=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Cart'
        verbose_name_plural = 'Carts'
        indexes = [
            models.Index(fields=['session_key', 'is_active']),
            models.Index(fields=['user', 'is_active']),
        ]

    def __str__(self):
        owner = self.user.email if self.user else f"Guest ({self.session_key[:8]})"
        return f"Cart {self.id} for {owner}"

    @property
    def total_items(self) -> int:
        return sum(item.quantity for item in self.items.all())

    @property
    def selected_items(self):
        return self.items.filter(is_selected=True)

    @property
    def subtotal(self) -> Decimal:
        return sum(item.line_total for item in self.selected_items)

class CartItem(TimeStampedModel):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    is_selected = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'
        constraints = [
            models.UniqueConstraint(
                fields=['cart', 'variant'],
                name='unique_cart_variant'
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gte=1),
                name='cart_item_quantity_positive'
            ),
        ]
        indexes = [
            models.Index(fields=['cart', 'is_selected']),
        ]

    def __str__(self):
        return f"{self.quantity}x {self.variant.sku} in Cart {self.cart.id}"

    @property
    def line_total(self) -> Decimal:
        return self.variant.effective_price * self.quantity
