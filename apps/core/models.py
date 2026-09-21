from django.db import models
from .files import image_path

class Technology(models.TextChoices):
    FDM = 'fdm', 'Filamento / FDM'
    RESIN = 'resin', 'Resina'

class SiteConfiguration(models.Model):
    name = models.CharField('nombre', max_length=100, default='Bijutsu Printing')
    logo = models.ImageField(upload_to=image_path, blank=True)
    email = models.EmailField('correo', blank=True)
    phone = models.CharField('teléfono', max_length=40, blank=True)
    address = models.CharField('dirección', max_length=255, blank=True)
    instagram = models.URLField(blank=True)
    whatsapp = models.URLField(blank=True)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'configuración del sitio'
        verbose_name_plural = 'configuración del sitio'
