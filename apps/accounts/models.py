from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.core.models import TimeStampedModel

class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=32, blank=True)
    telegram = models.CharField(max_length=64, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

class CustomerAddress(TimeStampedModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='addresses',
        null=True,
        blank=True
    )
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=32)
    telegram = models.CharField(max_length=64, blank=True)
    city_province = models.CharField(max_length=100, default='Phnom Penh')
    khan_district = models.CharField(max_length=100, blank=True)
    sangkat_commune = models.CharField(max_length=100, blank=True)
    street_address = models.CharField(max_length=255)
    landmark = models.CharField(max_length=255, blank=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Customer Address'
        verbose_name_plural = 'Customer Addresses'
        indexes = [
            models.Index(fields=['user', 'is_default']),
            models.Index(fields=['city_province', 'khan_district']),
        ]

    def __str__(self):
        return f"{self.full_name} - {self.city_province}, {self.khan_district or ''}"
