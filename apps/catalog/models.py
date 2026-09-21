from django.db import models
from django.core.validators import MinValueValidator
from django.urls import reverse
from apps.core.models import Technology
from apps.core.files import image_path, OptimizedImageMixin

class Category(OptimizedImageMixin, models.Model):
    name = models.CharField('nombre', max_length=100)
    slug = models.SlugField(unique=True)
    active = models.BooleanField('activa', default=True)
    order = models.PositiveIntegerField('orden', default=0)
    image = models.ImageField('imagen', upload_to=image_path, blank=True)
    thumbnail = models.ImageField(upload_to='thumbnails/', editable=False, blank=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'categoría'
        verbose_name_plural = 'categorías'

    def __str__(self):
        return self.name

class Product(OptimizedImageMixin, models.Model):
    class Kind(models.TextChoices):
        STANDARD = 'standard', 'Producto FDM / resina'
        KIT = 'kit', 'Model Kit'

    name = models.CharField('nombre', max_length=160)
    slug = models.SlugField(unique=True)
    short_description = models.CharField('descripción corta', max_length=255)
    description = models.TextField('descripción', blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, verbose_name='categoría')
    technology = models.CharField('tecnología', max_length=10, choices=Technology.choices)
    kind = models.CharField('tipo', max_length=15, choices=Kind.choices, default=Kind.STANDARD)
    base_price = models.DecimalField('precio base CLP', max_digits=12, decimal_places=0, validators=[MinValueValidator(0)])
    active = models.BooleanField('activo', default=True)
    featured = models.BooleanField('destacado', default=False)
    is_new = models.BooleanField('nuevo', default=False)
    is_demo = models.BooleanField('dato demo', default=False)
    order = models.PositiveIntegerField('orden', default=0)
    image = models.ImageField('imagen principal', upload_to=image_path, blank=True)
    thumbnail = models.ImageField(upload_to='thumbnails/', editable=False, blank=True)
    lead_time = models.CharField('tiempo de fabricación', max_length=100, blank=True)
    internal_notes = models.TextField('observaciones internas', blank=True)
    sku = models.CharField('código interno', max_length=60, blank=True)
    meta_title = models.CharField(max_length=160, blank=True)
    meta_description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'producto'
        constraints = [models.CheckConstraint(condition=models.Q(base_price__gte=0), name='product_nonnegative_price')]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('catalog:product', args=[self.slug])

    @property
    def cover(self):
        main = next((photo for photo in self.images.all() if photo.is_primary), None)
        return main.display_image if main else self.display_image

class ProductImage(OptimizedImageMixin, models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField('imagen', upload_to=image_path)
    thumbnail = models.ImageField(upload_to='thumbnails/', editable=False, blank=True)
    alt = models.CharField('texto alternativo', max_length=160)
    order = models.PositiveIntegerField('orden', default=0)
    is_primary = models.BooleanField('principal', default=False)

    class Meta:
        ordering = ['order', 'pk']
        constraints = [models.UniqueConstraint(fields=['product'], condition=models.Q(is_primary=True), name='one_primary_image')]

class ProductSpecification(models.Model):
    product = models.ForeignKey(Product, related_name='specifications', on_delete=models.CASCADE)
    label = models.CharField('propiedad (escala, altura, piezas...)', max_length=80)
    value = models.CharField('valor', max_length=160)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'pk']

class ProductOption(models.Model):
    product = models.ForeignKey(Product, related_name='options', on_delete=models.CASCADE)
    name = models.CharField('nombre', max_length=80)
    required = models.BooleanField('obligatoria', default=True)
    active = models.BooleanField('activa', default=True)
    order = models.PositiveIntegerField('orden', default=0)

    class Meta:
        ordering = ['order', 'pk']
        verbose_name = 'opción de producto'
        verbose_name_plural = 'opciones de producto'

    def __str__(self):
        return f'{self.product} · {self.name}'

class ProductOptionValue(models.Model):
    option = models.ForeignKey(ProductOption, related_name='values', on_delete=models.CASCADE)
    name = models.CharField('valor', max_length=100)
    surcharge = models.DecimalField('recargo CLP', max_digits=12, decimal_places=0, default=0, validators=[MinValueValidator(0)])
    active = models.BooleanField('activo', default=True)
    order = models.PositiveIntegerField('orden', default=0)

    class Meta:
        ordering = ['order', 'pk']
        verbose_name = 'valor de opción'
        verbose_name_plural = 'valores de opciones'
        constraints = [models.CheckConstraint(condition=models.Q(surcharge__gte=0), name='option_nonnegative_surcharge')]

    def __str__(self):
        return self.name
