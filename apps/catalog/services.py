from dataclasses import dataclass
from decimal import Decimal
from django.core.exceptions import ValidationError
from .models import ProductOptionValue

@dataclass(frozen=True)
class Estimate:
    unit: Decimal
    quantity: int
    total: Decimal
    values: list

def estimate(product, quantity, selections):
    if not product.active or not product.category.active:
        raise ValidationError('El producto no está disponible.')
    try:
        quantity = int(quantity)
        ids = [int(value) for value in selections]
    except (ValueError, TypeError):
        raise ValidationError('Configuración inválida.')
    if not 1 <= quantity <= 1000 or len(ids) != len(set(ids)):
        raise ValidationError('Cantidad u opciones inválidas.')
    values = list(ProductOptionValue.objects.filter(pk__in=ids, active=True, option__active=True, option__product=product).select_related('option'))
    option_ids = [v.option_id for v in values]
    required = set(product.options.filter(active=True, required=True).values_list('pk', flat=True))
    if len(values) != len(ids) or len(set(option_ids)) != len(option_ids) or not required.issubset(option_ids):
        raise ValidationError('Selecciona un valor válido para cada opción obligatoria.')
    unit = product.base_price + sum((v.surcharge for v in values), Decimal(0))
    return Estimate(unit, quantity, unit * quantity, values)
