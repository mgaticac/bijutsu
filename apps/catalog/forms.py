from django import forms
from .services import estimate

class ConfigurationForm(forms.Form):
    quantity = forms.IntegerField(label='Cantidad', min_value=1, max_value=1000, initial=1)

    def __init__(self, *args, product, **kwargs):
        super().__init__(*args, **kwargs)
        self.product = product
        for option in product.options.filter(active=True).prefetch_related('values'):
            self.fields[f'option_{option.pk}'] = forms.ModelChoiceField(
                label=option.name, queryset=option.values.filter(active=True), required=option.required,
                empty_label='Selecciona una opción' if option.required else 'Sin selección')

    def clean(self):
        data = super().clean()
        if not self.errors:
            data['estimate'] = estimate(self.product, data['quantity'], [value.pk for key, value in data.items() if key.startswith('option_') and value])
        return data
