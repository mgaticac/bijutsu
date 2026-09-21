from io import BytesIO
from pathlib import Path
import tempfile
import zipfile
from django.test import TestCase, override_settings
from django.contrib.auth.models import User, Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.urls import reverse
from apps.catalog.models import Category, Product, ProductOption, ProductOptionValue
from apps.core.files import private_storage
from .models import Quote, QuoteAttachment
from .validators import validate_attachment

OBJ = b'v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n'

class UploadTests(TestCase):
    def test_valid_obj(self):
        validate_attachment(SimpleUploadedFile('part.obj', OBJ, content_type='text/plain'))

    def test_invalid_content_extension_size_and_mime(self):
        for name, content, mime in [('x.exe', OBJ, 'application/octet-stream'), ('x.obj', b'<script>oops</script>', 'text/plain'),
                                    ('x.png', OBJ, 'image/png'), ('x.obj', OBJ, 'text/html'), ('x.obj', b'', 'text/plain')]:
            with self.assertRaises(ValidationError):
                validate_attachment(SimpleUploadedFile(name, content, content_type=mime))
        with override_settings(MAX_UPLOAD_BYTES=10), self.assertRaises(ValidationError):
            validate_attachment(SimpleUploadedFile('x.obj', OBJ, content_type='text/plain'))

    def test_zip_traversal_nested_archives_and_executables_rejected(self):
        for name, payload in [('../part.obj', OBJ), ('inner.zip', b'PK'), ('program.exe', b'MZ')]:
            buf = BytesIO()
            with zipfile.ZipFile(buf, 'w') as archive:
                archive.writestr(name, payload)
            with self.assertRaises(ValidationError):
                validate_attachment(SimpleUploadedFile('parts.zip', buf.getvalue(), content_type='application/zip'))

    def test_valid_zip(self):
        buf = BytesIO()
        with zipfile.ZipFile(buf, 'w') as archive:
            archive.writestr('models/part.obj', OBJ)
        validate_attachment(SimpleUploadedFile('parts.zip', buf.getvalue(), content_type='application/zip'))

    def test_3mf_container_and_xml_validation(self):
        for payload, valid in [(b'<model xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><resources/><build/></model>', True),
                               (b'<!DOCTYPE model [<!ENTITY x SYSTEM "file:///etc/passwd">]><model>&x;</model>', False),
                               (b'<html>not a model</html>', False)]:
            buf = BytesIO()
            with zipfile.ZipFile(buf, 'w') as archive:
                archive.writestr('3D/3dmodel.model', payload)
            file = SimpleUploadedFile('model.3mf', buf.getvalue(), content_type='model/3mf')
            if valid:
                validate_attachment(file)
            else:
                with self.assertRaises(ValidationError):
                    validate_attachment(file)

class QuoteFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('cliente', 'cliente@example.test', 'SecurePass!73')
        self.other = User.objects.create_user('otro', 'otro@example.test', 'SecurePass!74')
        category = Category.objects.create(name='Prueba', slug='prueba')
        self.product = Product.objects.create(name='Producto', slug='producto', category=category, technology='fdm', base_price=8000)
        self.option = ProductOption.objects.create(product=self.product, name='Tamaño')
        self.value = ProductOptionValue.objects.create(option=self.option, name='Grande', surcharge=3000)
        self.client.force_login(self.user)
        self.temp = tempfile.TemporaryDirectory()
        self.old_location = private_storage.location
        private_storage.__dict__['location'] = self.temp.name
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(lambda: private_storage.__dict__.update(location=self.old_location))

    def data(self):
        return {'name': 'Cliente', 'email': self.user.email, 'quantity': 2, f'option_{self.option.pk}': self.value.pk, 'estimated_total': '1', 'status': 'accepted'}

    def test_create_and_preserve_snapshot(self):
        response = self.client.post(reverse('quotes:create', args=[self.product.slug]), self.data())
        quote = Quote.objects.get()
        self.assertRedirects(response, reverse('quotes:detail', args=[quote.reference]))
        self.assertEqual(quote.estimated_total, 22000)
        self.assertEqual(quote.status, 'pending')
        self.product.base_price = 99999
        self.product.save()
        self.value.name = 'Modificado'
        self.value.save()
        self.assertEqual(quote.items.get().unit_price, 11000)
        self.assertEqual(quote.items.get().options.get().value, 'Grande')

    def test_invalid_options_create_nothing(self):
        data = self.data()
        data[f'option_{self.option.pk}'] = 99999
        response = self.client.post(reverse('quotes:create', args=[self.product.slug]), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Quote.objects.exists())

    def test_customer_isolation_and_private_download(self):
        quote = Quote.objects.create(customer=self.other, name='Otro', email=self.other.email)
        attachment = QuoteAttachment.objects.create(quote=quote, original_name='part.obj', file=SimpleUploadedFile('part.obj', OBJ))
        self.assertEqual(self.client.get(reverse('quotes:detail', args=[quote.reference])).status_code, 404)
        self.assertEqual(self.client.get(reverse('quotes:attachment', args=[attachment.pk])).status_code, 404)
        self.client.force_login(self.other)
        response = self.client.get(reverse('quotes:attachment', args=[attachment.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment;', response['Content-Disposition'])
        response.close()
        with self.assertRaises(ValueError):
            _ = attachment.file.url
        self.assertTrue(Path(attachment.file.path).is_relative_to(Path(self.temp.name)))

    def test_custom_request_requires_model_and_has_no_estimate(self):
        data = {'name': 'Cliente', 'email': self.user.email, 'technology': 'fdm', 'quantity': 3}
        response = self.client.post(reverse('quotes:custom'), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Quote.objects.exists())
        data['attachments'] = SimpleUploadedFile('model.obj', OBJ, content_type='text/plain')
        response = self.client.post(reverse('quotes:custom'), data)
        self.assertEqual(response.status_code, 302)
        quote = Quote.objects.get()
        self.assertIsNone(quote.estimated_total)
        self.assertEqual(quote.attachments.count(), 1)

    def test_multiple_uploads_all_validated(self):
        data = {'name': 'Cliente', 'email': self.user.email, 'technology': 'fdm', 'quantity': 3,
            'attachments': [SimpleUploadedFile('good.obj', OBJ, content_type='text/plain'),
                            SimpleUploadedFile('bad.obj', b'bad', content_type='text/plain')]}
        self.client.post(reverse('quotes:custom'), data)
        self.assertFalse(Quote.objects.exists())
        self.assertFalse(QuoteAttachment.objects.exists())

    def test_customer_can_only_accept_confirmed_quoted_own_request(self):
        quote = Quote.objects.create(customer=self.user, name='Cliente', email=self.user.email)
        url = reverse('quotes:respond', args=[quote.reference])
        self.client.post(url, {'decision': 'accepted'})
        quote.refresh_from_db()
        self.assertEqual(quote.status, 'pending')
        quote.status = 'quoted'
        quote.confirmed_total = 15000
        quote.save()
        self.client.post(url, {'decision': 'accepted'})
        quote.refresh_from_db()
        self.assertEqual(quote.status, 'accepted')
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(url, {'decision': 'rejected'}).status_code, 404)

    def test_anonymous_submission_redirects_to_login(self):
        self.client.logout()
        self.assertEqual(self.client.post(reverse('quotes:custom'), {}).status_code, 302)

    def test_csrf_enforced(self):
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(reverse('quotes:create', args=[self.product.slug]), self.data()).status_code, 403)

    def test_admin_detail_and_download_permission(self):
        quote = Quote.objects.create(customer=self.other, name='Otro', email=self.other.email)
        attachment = QuoteAttachment.objects.create(quote=quote, original_name='part.obj', file=SimpleUploadedFile('part.obj', OBJ))
        self.user.is_staff = True
        self.user.save()
        download = reverse('quotes:attachment', args=[attachment.pk])
        self.assertEqual(self.client.get(download).status_code, 404)
        self.user.user_permissions.add(Permission.objects.get(codename='view_quote'))
        response = self.client.get(download)
        self.assertEqual(response.status_code, 200)
        response.close()
        self.user.is_superuser = True
        self.user.save()
        self.assertContains(self.client.get(reverse('management:edit', args=['cotizaciones', quote.pk])), 'Descargar')

    @override_settings(MAX_UPLOAD_BYTES=10)
    def test_stream_limit_rejects_before_persistence(self):
        response = self.client.post(reverse('quotes:custom'), {'name': 'Cliente', 'email': self.user.email,
            'technology': 'fdm', 'quantity': 1, 'attachments': SimpleUploadedFile('part.obj', OBJ, content_type='text/plain')})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Quote.objects.exists())
