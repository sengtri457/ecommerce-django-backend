from django.db import models
from apps.core.models import TimeStampedModel
from apps.catalog.models import ProductVariant

class StockMovement(TimeStampedModel):
    MOVEMENT_TYPES = (
        ('PURCHASE', 'Customer Purchase'),
        ('RESTOCK', 'Inventory Restock'),
        ('RETURN', 'Order Return'),
        ('ADJUSTMENT', 'Manual Adjustment'),
    )

    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name='stock_movements'
    )
    quantity_change = models.IntegerField()
    movement_type = models.CharField(max_length=30, choices=MOVEMENT_TYPES)
    reference_id = models.CharField(max_length=100, blank=True)
    balance_after = models.PositiveIntegerField()
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Stock Movement'
        verbose_name_plural = 'Stock Movements'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['variant', 'created_at']),
            models.Index(fields=['reference_id']),
        ]

    def __str__(self):
        return f"{self.variant.sku} | {self.movement_type} ({self.quantity_change}) -> Balance: {self.balance_after}"
