import uuid
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator
from apps.core.files import private_storage, attachment_path
from apps.core.models import Technology
from .validators import validate_attachment

class Quote(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendiente'
        REVIEW = 'review', 'En revisión'
        QUOTED = 'quoted', 'Cotizado'
        ACCEPTED = 'accepted', 'Aceptado'
        REJECTED = 'rejected', 'Rechazado'
        PRODUCTION = 'production', 'En producción'
        FINISHED = 'finished', 'Terminado'
        DELIVERED = 'delivered', 'Entregado'
        CANCELLED = 'cancelled', 'Cancelado'

    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='quotes')
    name = models.CharField('nombre', max_length=150)
    email = models.EmailField('correo')
    phone = models.CharField('teléfono', max_length=40, blank=True)
    technology = models.CharField('tecnología', max_length=10, choices=Technology.choices, blank=True)
    quantity = models.PositiveIntegerField('cantidad', default=1, validators=[MinValueValidator(1)])
    color = models.CharField(max_length=100, blank=True)
    material = models.CharField(max_length=100, blank=True)
    size = models.CharField('tamaño aproximado', max_length=100, blank=True)
    comments = models.TextField('comentarios', blank=True, max_length=5000)
    internal_notes = models.TextField('notas internas', blank=True)
    estimated_total = models.DecimalField('total estimado', max_digits=14, decimal_places=0, null=True, blank=True)
    confirmed_total = models.DecimalField('total confirmado', max_digits=14, decimal_places=0, null=True, blank=True, validators=[MinValueValidator(0)])
    status = models.CharField('estado', max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'cotización'
        verbose_name_plural = 'cotizaciones'
        constraints = [
            models.CheckConstraint(condition=models.Q(quantity__gte=1), name='quote_positive_quantity'),
            models.CheckConstraint(condition=models.Q(confirmed_total__gte=0) | models.Q(confirmed_total__isnull=True), name='quote_valid_confirmed_total'),
        ]

    def __str__(self):
        return f'BP-{self.pk:05d}' if self.pk else 'Nueva cotización'

class QuoteItem(models.Model):
    quote = models.ForeignKey(Quote, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('catalog.Product', null=True, blank=True, on_delete=models.SET_NULL)
    product_name = models.CharField(max_length=160)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=12, decimal_places=0)

    @property
    def total(self):
        return self.unit_price * self.quantity

class QuoteItemOption(models.Model):
    item = models.ForeignKey(QuoteItem, related_name='options', on_delete=models.CASCADE)
    name = models.CharField(max_length=80)
    value = models.CharField(max_length=100)
    surcharge = models.DecimalField(max_digits=12, decimal_places=0)

class QuoteAttachment(models.Model):
    quote = models.ForeignKey(Quote, related_name='attachments', on_delete=models.CASCADE)
    file = models.FileField(storage=private_storage, upload_to=attachment_path, validators=[validate_attachment])
    original_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
