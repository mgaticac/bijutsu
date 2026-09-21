from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify
from apps.catalog.models import Category, Product, ProductOption, ProductOptionValue, ProductSpecification
from apps.core.models import SiteConfiguration

class Command(BaseCommand):
    help = 'Crea datos demo de desarrollo, sin sobrescribir cambios ni crear cuentas.'

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('Los datos demo solo se cargan con DEBUG=True.')
        SiteConfiguration.objects.get_or_create(pk=1)
        names = ['Clickers', 'Fidgets', 'Sensoriales', 'Articulados', 'Figuras', 'Figuras multicolor',
                 'Decoración', 'Posavasos', 'Organizadores', 'Accesorios', 'Model Kits', 'Miniaturas', 'Bustos', 'Otros']
        categories = {}
        for index, name in enumerate(names):
            categories[name], _ = Category.objects.get_or_create(slug=slugify(name), defaults={'name': name, 'order': index})
        rows = [
            ('Clicker geométrico', 'Clickers', 'fdm', 'standard', 3500),
            ('Fidget orbital', 'Fidgets', 'fdm', 'standard', 5500),
            ('Dragón articulado', 'Articulados', 'fdm', 'standard', 8000),
            ('Posavasos de líneas', 'Posavasos', 'fdm', 'standard', 4000),
            ('Figura geométrica multicolor', 'Figuras multicolor', 'fdm', 'standard', 12990),
            ('Model Kit abstracto', 'Model Kits', 'resin', 'kit', 28000),
            ('Miniatura geométrica', 'Miniaturas', 'resin', 'standard', 6000),
        ]
        for index, (name, category, technology, kind, price) in enumerate(rows):
            product, created = Product.objects.get_or_create(slug=slugify(name), defaults={
                'name': name, 'category': categories[category], 'technology': technology, 'kind': kind,
                'base_price': price, 'short_description': 'Producto de demostración para probar la configuración y las cotizaciones.',
                'description': 'Datos de desarrollo. Las opciones y los precios son ejemplos; no representan una oferta comercial real.',
                'featured': index in (0, 1, 2, 5), 'is_new': index > 3, 'is_demo': True, 'order': index,
            })
            if not created:
                continue
            if kind == 'kit':
                variants = {'Escala': [('1/12', 0), ('1/8', 12000)], 'Versión': [('Kit completo', 0), ('Kit con base', 3000)]}
                for label, value in [('Estado', 'Sin ensamblar'), ('Material', 'Resina'), ('Altura aproximada', 'Según escala seleccionada')]:
                    ProductSpecification.objects.create(product=product, label=label, value=value)
            elif technology == 'fdm':
                variants = {'Tamaño': [('Estándar', 0), ('Grande', 3000)], 'Color': [('Negro', 0), ('Blanco', 0), ('Multicolor', 2500)], 'Material': [('PLA', 0), ('PETG', 1500)]}
            else:
                variants = {'Tamaño': [('Estándar', 0), ('Grande', 2000)]}
            for position, (label, values) in enumerate(variants.items()):
                option = ProductOption.objects.create(product=product, name=label, order=position)
                for order, (value, surcharge) in enumerate(values):
                    ProductOptionValue.objects.create(option=option, name=value, surcharge=surcharge, order=order)
        self.stdout.write(self.style.SUCCESS('Datos demo disponibles. No se crearon usuarios ni fotografías ficticias.'))
