from django import forms
from django.core.exceptions import ValidationError
from .models import Quote
from .validators import validate_attachment

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        if not data:
            return []
        files = data if isinstance(data, (list, tuple)) else [data]
        if len(files) > 5:
            raise ValidationError('Adjunta como máximo 5 archivos.')
        cleaned = []
        for file in files:
            clean = super().clean(file, initial)
            validate_attachment(clean)
            cleaned.append(clean)
        return cleaned

class QuoteForm(forms.ModelForm):
    attachments = MultipleFileField(label='Archivos y referencias', required=False,
        help_text='Hasta 5 archivos, 25 MB cada uno: STL, OBJ, 3MF, ZIP, JPG, PNG o WebP.')

    class Meta:
        model = Quote
        fields = ['name', 'email', 'phone', 'comments']
        widgets = {'comments': forms.Textarea(attrs={'rows': 4})}

class CustomPrintForm(QuoteForm):
    class Meta(QuoteForm.Meta):
        fields = ['name', 'email', 'phone', 'technology', 'quantity', 'color', 'material', 'size', 'comments']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['technology'].required = True
        self.fields['quantity'].max_value = 1000

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if quantity > 1000:
            raise ValidationError('El máximo es 1000 unidades.')
        return quantity

    def clean_attachments(self):
        files = self.cleaned_data['attachments']
        if not any(f.name.lower().endswith(('.stl', '.obj', '.3mf', '.zip')) for f in files):
            raise ValidationError('Adjunta al menos un modelo STL, OBJ, 3MF o ZIP con modelos.')
        return files
