from django.db import transaction
from django.core.exceptions import ValidationError
from apps.quotes.models import Quote
from .models import Order, OrderItem

@transaction.atomic
def convert_quote(quote):
    quote = Quote.objects.select_for_update().get(pk=quote.pk)
    existing = Order.objects.filter(quote=quote).first()
    if existing:
        return existing
    if quote.status != Quote.Status.ACCEPTED or quote.confirmed_total is None:
        raise ValidationError('La cotización debe estar aceptada y tener un total confirmado.')
    order = Order.objects.create(quote=quote, total=quote.confirmed_total)
    for item in quote.items.prefetch_related('options'):
        OrderItem.objects.create(order=order, name=item.product_name, quantity=item.quantity,
            unit_estimate=item.unit_price, configuration={v.name: v.value for v in item.options.all()})
    if not order.items.exists():
        OrderItem.objects.create(order=order, name='Impresión de archivo propio', quantity=quote.quantity,
            configuration={'tecnología': quote.get_technology_display(), 'color': quote.color, 'material': quote.material, 'tamaño': quote.size})
    return order
