from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.urls import reverse
from .models import Category, Product, ProductOption, ProductOptionValue
from .services import estimate

class PricingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name='Prueba', slug='prueba')
        cls.product = Product.objects.create(name='Dragón', slug='dragon', category=cls.category, technology='fdm', base_price=8000)
        cls.size = ProductOption.objects.create(product=cls.product, name='Tamaño')
        cls.large = ProductOptionValue.objects.create(option=cls.size, name='Grande', surcharge=3000)
        cls.color = ProductOption.objects.create(product=cls.product, name='Color')
        cls.multi = ProductOptionValue.objects.create(option=cls.color, name='Multicolor', surcharge=2500)

    def test_price_uses_server_values(self):
        result = estimate(self.product, 2, [self.large.pk, self.multi.pk])
        self.assertEqual(result.unit, Decimal(13500))
        self.assertEqual(result.total, Decimal(27000))

    def test_required_and_duplicate_options(self):
        for choices in [[], [self.large.pk], [self.large.pk, self.large.pk, self.multi.pk]]:
            with self.assertRaises(ValidationError):
                estimate(self.product, 1, choices)

    def test_foreign_and_inactive_options(self):
        other = Product.objects.create(name='Otro', slug='otro', category=self.category, technology='fdm', base_price=100)
        foreign_option = ProductOption.objects.create(product=other, name='Tamaño')
        foreign = ProductOptionValue.objects.create(option=foreign_option, name='Único')
        with self.assertRaises(ValidationError):
            estimate(self.product, 1, [self.large.pk, self.multi.pk, foreign.pk])
        self.multi.active = False
        self.multi.save()
        with self.assertRaises(ValidationError):
            estimate(self.product, 1, [self.large.pk, self.multi.pk])

    def test_multiple_values_for_same_option(self):
        small = ProductOptionValue.objects.create(option=self.size, name='Pequeño')
        with self.assertRaises(ValidationError):
            estimate(self.product, 1, [small.pk, self.large.pk, self.multi.pk])

    def test_quantity_bounds(self):
        for quantity in [0, -1, 1001, '1.5', 'invalid']:
            with self.assertRaises(ValidationError):
                estimate(self.product, quantity, [self.large.pk, self.multi.pk])

    def test_estimation_endpoint_ignores_browser_price(self):
        response = self.client.post(reverse('catalog:estimate', args=[self.product.slug]), {
            'quantity': 2, f'option_{self.size.pk}': self.large.pk, f'option_{self.color.pk}': self.multi.pk, 'price': 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['total'], '27000')

    def test_inactive_category_hidden(self):
        self.category.active = False
        self.category.save()
        self.assertEqual(self.client.get(self.product.get_absolute_url()).status_code, 404)
        self.assertNotContains(self.client.get(reverse('catalog:list')), self.product.name)

    def test_bad_price_filters_do_not_crash(self):
        for value in ['NaN', 'Infinity', 'invalid', '-1', '1e100']:
            self.assertEqual(self.client.get(reverse('catalog:list'), {'max_price': value}).status_code, 200)

    def test_search_and_price_filter(self):
        self.assertContains(self.client.get(reverse('catalog:list'), {'q': 'Dragón'}), 'Dragón')
        self.assertNotContains(self.client.get(reverse('catalog:list'), {'max_price': '5000'}), 'Dragón')
