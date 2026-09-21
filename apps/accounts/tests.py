from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.core import mail
from django.urls import reverse

class AccountTests(TestCase):
    def test_registration_creates_profile(self):
        response = self.client.post(reverse('register'), {'username': 'cliente', 'email': 'cliente@example.test',
            'password1': 'SecureComplex!772', 'password2': 'SecureComplex!772'})
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='cliente')
        self.assertEqual(user.profile.phone, '')
        self.assertEqual(self.client.get(reverse('profile')).status_code, 200)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', DEFAULT_FROM_EMAIL='test@example.test')
    def test_password_reset_sends_link(self):
        User.objects.create_user('cliente', 'cliente@example.test', 'SecureComplex!772')
        response = self.client.post(reverse('password_reset'), {'email': 'cliente@example.test'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('/cuenta/reset/', mail.outbox[0].body)
