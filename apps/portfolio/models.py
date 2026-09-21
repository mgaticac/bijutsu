from django.db import models
from django.urls import reverse
from apps.core.models import Technology
from apps.core.files import image_path, OptimizedImageMixin

class PortfolioItem(OptimizedImageMixin, models.Model):
    title = models.CharField('título', max_length=160)
    slug = models.SlugField('enlace de la historia', unique=True, max_length=180)
    description = models.TextField('resumen', blank=True)
    body = models.TextField('historia y experiencia', blank=True, help_text='Cuenta el proceso, las pruebas, dificultades y lo que aprendiste. Separa los párrafos con una línea en blanco.')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    technology = models.CharField('tecnología', max_length=10, choices=Technology.choices)
    category = models.ForeignKey('catalog.Category', blank=True, null=True, on_delete=models.SET_NULL)
    image = models.ImageField('fotografía', upload_to=image_path, blank=True)
    thumbnail = models.ImageField(upload_to='thumbnails/', editable=False, blank=True)
    date = models.DateField('fecha', blank=True, null=True)
    featured = models.BooleanField('destacado', default=False)
    active = models.BooleanField('publicada', default=False)
    order = models.PositiveIntegerField('orden', default=0)

    class Meta:
        ordering = ['order', '-pk']
        verbose_name = 'trabajo realizado'
        verbose_name_plural = 'trabajos realizados'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('story', args=[self.slug])

class PortfolioImage(OptimizedImageMixin, models.Model):
    item = models.ForeignKey(PortfolioItem, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to=image_path)
    thumbnail = models.ImageField(upload_to='thumbnails/', editable=False, blank=True)
    alt = models.CharField(max_length=160)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'pk']
