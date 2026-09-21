from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from apps.quotes.models import Quote, QuoteItem, QuoteItemOption
from .services import convert_quote
from .models import Order

class ConversionTests(TestCase):
    def setUp(self):
        user = User.objects.create_user('client')
        self.quote = Quote.objects.create(customer=user, name='Cliente', email='c@example.test')

    def test_must_be_accepted_with_confirmed_price(self):
        for status, price in [('pending', None), ('quoted', 15000), ('accepted', None)]:
            self.quote.status = status
            self.quote.confirmed_total = price
            self.quote.save()
            with self.assertRaises(ValidationError):
                convert_quote(self.quote)
        self.assertFalse(Order.objects.exists())

    def test_conversion_is_idempotent_and_copies_items(self):
        self.quote.status = 'accepted'
        self.quote.confirmed_total = 12000
        self.quote.save()
        item = QuoteItem.objects.create(quote=self.quote, product_name='Figura', quantity=2, unit_price=5500)
        QuoteItemOption.objects.create(item=item, name='Color', value='Negro', surcharge=0)
        order = convert_quote(self.quote)
        self.assertEqual(order.total, 12000)
        self.assertEqual(order.items.get().configuration, {'Color': 'Negro'})
        self.assertEqual(convert_quote(self.quote).pk, order.pk)
        self.assertEqual(Order.objects.count(), 1)

    def test_custom_file_order_keeps_quantity(self):
        self.quote.status = 'accepted'
        self.quote.confirmed_total = 15000
        self.quote.quantity = 7
        self.quote.save()
        self.assertEqual(convert_quote(self.quote).items.get().quantity, 7)
