from io import BytesIO
import tempfile
from PIL import Image
from django.contrib.auth.models import User, Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings, Client
from django.urls import reverse
from apps.catalog.models import Category, Product, ProductOption, ProductOptionValue
from apps.portfolio.models import PortfolioItem
from apps.quotes.models import Quote
from apps.orders.models import Order
from apps.core.models import SiteConfiguration

def picture():
    stream = BytesIO()
    Image.new('RGB', (32, 32), 'red').save(stream, 'PNG')
    return SimpleUploadedFile('cover.png', stream.getvalue(), content_type='image/png')

def management(prefix, total=0, initial=0):
    return {f'{prefix}-TOTAL_FORMS': total, f'{prefix}-INITIAL_FORMS': initial,
            f'{prefix}-MIN_NUM_FORMS': 0, f'{prefix}-MAX_NUM_FORMS': 1000}

class ManagementTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('owner', 'owner@example.test', 'ComplexPass!23')
        self.customer = User.objects.create_user('client', 'client@example.test', 'ComplexPass!24')
        self.client.force_login(self.admin)
        self.category = Category.objects.create(name='Prueba', slug='prueba')
        self.product = Product.objects.create(name='Producto', slug='producto', technology='fdm', category=self.category, base_price=8000)
        self.tmp = tempfile.TemporaryDirectory()
        self.override = override_settings(MEDIA_ROOT=self.tmp.name)
        self.override.enable()
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(self.override.disable)

    def test_every_management_screen_renders_without_django_admin_links(self):
        for section in ['productos', 'categorias', 'opciones', 'historias', 'cotizaciones', 'pedidos', 'clientes']:
            response = self.client.get(reverse('management:list', args=[section]))
            self.assertEqual(response.status_code, 200, section)
            self.assertNotContains(response, 'href="/admin/')
        for section in ['productos', 'categorias', 'opciones', 'historias']:
            self.assertEqual(self.client.get(reverse('management:create', args=[section])).status_code, 200)
        self.assertEqual(self.client.get(reverse('management:settings')).status_code, 200)

    def test_customer_and_unauthenticated_access_blocked(self):
        url = reverse('management:edit', args=['productos', self.product.pk])
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url, {'name': 'hacked'}).status_code, 403)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Producto')

    def test_staff_permissions_checked_on_each_screen(self):
        self.customer.is_staff = True
        self.customer.save()
        self.customer.user_permissions.add(Permission.objects.get(codename='view_product'))
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(reverse('management:list', args=['productos'])).status_code, 200)
        self.assertEqual(self.client.post(reverse('management:create', args=['productos']), {}).status_code, 403)
        self.assertEqual(self.client.get(reverse('management:list', args=['clientes'])).status_code, 403)
        self.assertEqual(self.client.post(reverse('management:settings'), {}).status_code, 403)

    def test_create_product_with_images_and_specifications(self):
        payload = {'name': 'Nuevo', 'slug': 'nuevo', 'short_description': 'Prueba', 'category': self.category.pk,
            'technology': 'fdm', 'kind': 'standard', 'base_price': 15000, 'active': 'on', 'order': 0,
            **management('images', 1), 'images-0-image': picture(), 'images-0-alt': 'Foto de prueba',
            'images-0-order': 0, 'images-0-is_primary': 'on', **management('specs', 1),
            'specs-0-label': 'Altura', 'specs-0-value': '20 cm', 'specs-0-order': 0}
        response = self.client.post(reverse('management:create', args=['productos']), payload)
        self.assertEqual(response.status_code, 302)
        product = Product.objects.get(slug='nuevo')
        self.assertEqual(product.images.get().alt, 'Foto de prueba')
        self.assertEqual(product.specifications.get().value, '20 cm')

    def test_options_and_prices_editable(self):
        payload = {'product': self.product.pk, 'name': 'Color', 'required': 'on', 'active': 'on', 'order': 0,
            **management('values', 1), 'values-0-name': 'Multicolor', 'values-0-surcharge': 2500, 'values-0-active': 'on', 'values-0-order': 0}
        response = self.client.post(reverse('management:create', args=['opciones']), payload)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ProductOptionValue.objects.get().surcharge, 2500)

    def test_foreign_inline_ids_cannot_be_attached_or_modified(self):
        own = ProductOption.objects.create(product=self.product, name='Color')
        other = ProductOption.objects.create(product=self.product, name='Material')
        value = ProductOptionValue.objects.create(option=other, name='PLA', surcharge=500)
        data = {'product': self.product.pk, 'name': 'Color', 'required': 'on', 'active': 'on', 'order': 0,
            **management('values', 1, 1), 'values-0-id': value.pk, 'values-0-name': 'Hacked',
            'values-0-surcharge': 1, 'values-0-active': 'on', 'values-0-order': 0}
        response = self.client.post(reverse('management:edit', args=['opciones', own.pk]), data)
        self.assertEqual(response.status_code, 200)
        value.refresh_from_db()
        self.assertEqual(value.name, 'PLA')
        self.assertEqual(value.option_id, other.pk)

    def test_child_permission_prevents_partial_parent_save(self):
        self.customer.is_staff = True
        self.customer.save()
        self.customer.user_permissions.add(*Permission.objects.filter(codename__in=['view_productoption', 'change_productoption', 'view_productoptionvalue']))
        self.client.force_login(self.customer)
        option = ProductOption.objects.create(product=self.product, name='Color')
        data = {'product': self.product.pk, 'name': 'Changed', 'required': 'on', 'active': 'on', 'order': 0,
            **management('values', 1), 'values-0-name': 'Multicolor', 'values-0-surcharge': 2500, 'values-0-active': 'on', 'values-0-order': 0}
        response = self.client.post(reverse('management:edit', args=['opciones', option.pk]), data)
        self.assertEqual(response.status_code, 403)
        option.refresh_from_db()
        self.assertEqual(option.name, 'Color')
        self.assertFalse(ProductOptionValue.objects.exists())

    def test_story_draft_without_photo_and_publication_validation(self):
        data = {'title': 'Borrador sin foto', 'slug': 'borrador', 'body': 'Texto inicial.',
            'technology': 'fdm', 'order': 0, **management('gallery')}
        self.assertEqual(self.client.post(reverse('management:create', args=['historias']), data).status_code, 302)
        story = PortfolioItem.objects.get()
        data['active'] = 'on'
        response = self.client.post(reverse('management:edit', args=['historias', story.pk]), data)
        self.assertContains(response, 'Agrega una fotografía de portada antes de publicar.')
        story.refresh_from_db()
        self.assertFalse(story.active)

    def test_delete_requires_post_and_protected_category_is_handled(self):
        url = reverse('management:delete', args=['productos', self.product.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertTrue(Product.objects.filter(pk=self.product.pk).exists())
        response = self.client.post(reverse('management:delete', args=['categorias', self.category.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())
        self.assertEqual(self.client.post(url).status_code, 302)
        self.assertFalse(Product.objects.filter(pk=self.product.pk).exists())

    def test_quote_review_conversion_and_order_status(self):
        quote = Quote.objects.create(customer=self.customer, name='Cliente', email=self.customer.email)
        edit = reverse('management:edit', args=['cotizaciones', quote.pk])
        self.assertEqual(self.client.post(edit, {'status': 'quoted', 'confirmed_total': ''}).status_code, 200)
        quote.refresh_from_db()
        self.assertEqual(quote.status, 'pending')
        self.assertEqual(self.client.post(edit, {'status': 'accepted', 'confirmed_total': 12500, 'internal_notes': 'Solo taller'}).status_code, 302)
        convert = reverse('management:convert', args=[quote.pk])
        self.assertEqual(self.client.get(convert).status_code, 405)
        self.client.post(convert)
        self.client.post(convert)
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.get()
        self.client.post(reverse('management:edit', args=['pedidos', order.pk]), {'status': 'printing'})
        order.refresh_from_db()
        self.assertEqual(order.status, 'printing')
        self.client.force_login(self.customer)
        response = self.client.get(reverse('quotes:detail', args=[quote.reference]))
        self.assertNotContains(response, 'Solo taller')
        self.assertContains(response, 'Imprimiendo')

    def test_customer_edit_cannot_promote_to_staff(self):
        response = self.client.post(reverse('management:edit', args=['clientes', self.customer.pk]),
            {'first_name': 'Ana', 'last_name': '', 'email': 'client@example.test', 'is_active': 'on',
             'is_staff': 'on', 'is_superuser': 'on', 'phone': '12345'})
        self.assertEqual(response.status_code, 302)
        self.customer.refresh_from_db()
        self.assertFalse(self.customer.is_staff)
        self.assertFalse(self.customer.is_superuser)
        self.assertEqual(self.customer.profile.phone, '12345')
        self.assertEqual(self.client.get(reverse('management:edit', args=['clientes', self.admin.pk])).status_code, 404)

    def test_configuration_saved(self):
        self.client.post(reverse('management:settings'), {'name': 'Bijutsu Printing', 'email': '', 'phone': '', 'address': '', 'instagram': '', 'whatsapp': ''})
        self.assertEqual(SiteConfiguration.objects.get().name, 'Bijutsu Printing')

    def test_csrf_protects_management(self):
        browser = Client(enforce_csrf_checks=True)
        browser.force_login(self.admin)
        self.assertEqual(browser.post(reverse('management:create', args=['categorias']), {'name': 'oops'}).status_code, 403)

    def test_story_draft_publication_body_and_gallery(self):
        payload = {'title': 'Una experiencia', 'slug': 'una-experiencia', 'description': 'Resumen del taller',
            'body': 'Primer intento.\n\nAprendí a ajustar los soportes. <script>alert(1)</script>',
            'image': picture(), 'technology': 'fdm', 'order': 0, **management('gallery', 1),
            'gallery-0-image': picture(), 'gallery-0-alt': 'El proceso', 'gallery-0-order': 0}
        response = self.client.post(reverse('management:create', args=['historias']), payload)
        self.assertEqual(response.status_code, 302)
        story = PortfolioItem.objects.get()
        self.assertFalse(story.active)
        self.assertEqual(self.client.get(story.get_absolute_url()).status_code, 404)
        self.assertNotContains(self.client.get(reverse('portfolio')), story.title)
        story.active = True
        story.save()
        self.client.logout()
        response = self.client.get(story.get_absolute_url())
        self.assertContains(response, 'Aprendí a ajustar los soportes.')
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertContains(response, 'El proceso')
        self.assertContains(self.client.get(reverse('portfolio')), story.title)
