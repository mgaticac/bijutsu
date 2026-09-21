from django.db import models
from django.core.validators import MinValueValidator

class Order(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = 'confirmed', 'Confirmado'
        QUEUED = 'queued', 'En cola'
        PRINTING = 'printing', 'Imprimiendo'
        FINISHING = 'finishing', 'Postprocesado'
        READY = 'ready', 'Listo'
        DELIVERED = 'delivered', 'Entregado'
        CANCELLED = 'cancelled', 'Cancelado'

    quote = models.OneToOneField('quotes.Quote', on_delete=models.PROTECT, related_name='order')
    total = models.DecimalField(max_digits=14, decimal_places=0, validators=[MinValueValidator(0)])
    status = models.CharField('estado', max_length=20, choices=Status.choices, default=Status.CONFIRMED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'pedido'
        ordering = ['-created_at']

    def __str__(self):
        return f'Pedido {self.pk} · {self.quote}'

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    name = models.CharField(max_length=160)
    quantity = models.PositiveIntegerField()
    unit_estimate = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)
    configuration = models.JSONField(default=dict)
