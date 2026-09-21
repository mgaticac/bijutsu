from django import template
register = template.Library()

@register.filter
def clp(value):
    if value is None:
        return 'Por confirmar'
    return '$' + f'{value:,.0f}'.replace(',', '.')
