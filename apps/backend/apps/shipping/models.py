from django.db import models


class ShippingZone(models.Model):
    municipality = models.CharField(max_length=100, unique=True)
    fee = models.DecimalField(max_digits=12, decimal_places=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "shipping_zones"
        verbose_name = "Zona de envío"
        verbose_name_plural = "Zonas de envío"
        ordering = ["municipality"]

    def __str__(self) -> str:
        return self.municipality
