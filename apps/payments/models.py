from django.db import models
from apps.core.models import TimeStampedModel, UUIDModel
from apps.orders.models import Order

class Payment(TimeStampedModel, UUIDModel):
    PAYMENT_METHOD_CHOICES = (
        ('KHQR', 'Bakong KHQR'),
        ('COD', 'Cash on Delivery'),
        ('CARD', 'Credit / Debit Card'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('PENDING', 'Pending Payment'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    amount_usd = models.DecimalField(max_digits=10, decimal_places=2)
    amount_khr = models.BigIntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='PENDING'
    )
    transaction_reference = models.CharField(
        max_length=120,
        unique=True,
        null=True,
        blank=True
    )
    khqr_md5 = models.CharField(max_length=64, blank=True)
    khqr_payload = models.TextField(blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order', 'status']),
            models.Index(fields=['transaction_reference']),
            models.Index(fields=['khqr_md5']),
        ]

    def __str__(self):
        return f"{self.payment_method} Payment ({self.status}) for Order {self.order.order_number}"

class PaymentTransaction(TimeStampedModel):
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    action = models.CharField(max_length=50)
    raw_data = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = 'Payment Transaction'
        verbose_name_plural = 'Payment Transactions'
        ordering = ['-created_at']

    def __str__(self):
        return f"Transaction {self.action} on Payment {self.payment.id}"
