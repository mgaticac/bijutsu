from django.test import TestCase, override_settings
from django.core.management import call_command
from django.contrib.auth.models import User
from django.urls import reverse
from apps.catalog.models import Product
from apps.core.templatetags.money import clp
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from pathlib import Path
import tempfile
from PIL import Image
from apps.catalog.models import Category

@override_settings(DEBUG=True)
class PageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', verbosity=0)

    def test_public_pages(self):
        for url in ['/', '/catalogo/', '/filamento/', '/resina/', '/model-kits/', '/trabajos/', '/cuenta/login/', '/cuenta/registro/', '/cuenta/password_reset/']:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
        for product in Product.objects.all():
            self.assertContains(self.client.get(product.get_absolute_url()), product.name)

    def test_seed_idempotent(self):
        count = Product.objects.count()
        call_command('seed_demo', verbosity=0)
        self.assertEqual(Product.objects.count(), count)

    def test_clp(self):
        self.assertEqual(clp(12990), '$12.990')
        self.assertEqual(clp(None), 'Por confirmar')

    def test_dashboard_permissions_and_admin_pages(self):
        user = User.objects.create_user('normal', password='StrongPass!23')
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse('dashboard')).status_code, 403)
        user.is_staff = True
        user.save()
        self.assertEqual(self.client.get(reverse('dashboard')).status_code, 403)
        user.is_superuser = True
        user.save()
        self.assertEqual(self.client.get(reverse('dashboard')).status_code, 200)
        for url in ['/gestion/', '/gestion/productos/', '/gestion/productos/nuevo/', '/gestion/cotizaciones/', '/gestion/configuracion/']:
            self.assertEqual(self.client.get(url).status_code, 200)
        self.assertRedirects(self.client.get('/admin/'), '/gestion/')
        self.assertEqual(self.client.get('/admin/catalog/product/').status_code, 404)

class ImageTests(TestCase):
    def test_original_preserved_and_thumbnail_bounded(self):
        with tempfile.TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            buffer = BytesIO()
            Image.new('RGB', (1800, 1200), 'white').save(buffer, 'JPEG')
            category = Category.objects.create(name='Imágenes', slug='imagenes',
                image=SimpleUploadedFile('photo.jpg', buffer.getvalue(), content_type='image/jpeg'))
            self.assertTrue(Path(category.image.path).exists())
            with Image.open(category.image.path) as original:
                self.assertEqual(original.size, (1800, 1200))
            with Image.open(category.thumbnail.path) as thumbnail:
                self.assertEqual(thumbnail.size, (900, 600))
                self.assertEqual(thumbnail.format, 'WEBP')
