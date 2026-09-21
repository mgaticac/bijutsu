from django import forms
from django.contrib.auth.models import User
from django.forms import inlineformset_factory, BaseInlineFormSet
from apps.catalog.models import Category, Product, ProductImage, ProductSpecification, ProductOption, ProductOptionValue
from apps.portfolio.models import PortfolioItem, PortfolioImage
from apps.quotes.models import Quote
from apps.orders.models import Order
from apps.core.models import SiteConfiguration
from .widgets import ImagePreviewInput

class ManagementForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field, forms.ImageField):
                field.widget = ImagePreviewInput(attrs={'accept': 'image/*'})

class ProductForm(ManagementForm):
    class Meta:
        model = Product
        fields = ['name', 'slug', 'short_description', 'description', 'category', 'technology', 'kind',
                  'base_price', 'image', 'lead_time', 'active', 'featured', 'is_new', 'is_demo', 'order',
                  'sku', 'internal_notes', 'meta_title', 'meta_description']
        widgets = {key: forms.Textarea(attrs={'rows': 4}) for key in ['description', 'internal_notes']}

class CategoryForm(ManagementForm):
    class Meta:
        model = Category
        fields = ['name', 'slug', 'image', 'active', 'order']

class OptionForm(forms.ModelForm):
    class Meta:
        model = ProductOption
        fields = ['product', 'name', 'required', 'active', 'order']

class StoryForm(ManagementForm):
    class Meta:
        model = PortfolioItem
        fields = ['title', 'slug', 'description', 'body', 'image', 'technology', 'category', 'date', 'active', 'featured', 'order']
        widgets = {'body': forms.Textarea(attrs={'rows': 18, 'placeholder': 'Cada impresión tiene una historia. Escribe aquí la tuya…'}),
                   'description': forms.Textarea(attrs={'rows': 3}), 'date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')}
        labels = {'image': 'Fotografía de portada', 'active': 'Publicar historia (desmarca para guardar como borrador)'}

    def clean(self):
        data = super().clean()
        if data.get('active'):
            if not data.get('image'):
                self.add_error('image', 'Agrega una fotografía de portada antes de publicar.')
            if not data.get('body', '').strip():
                self.add_error('body', 'Escribe la historia antes de publicarla.')
        return data

class QuoteManagementForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = ['status', 'confirmed_total', 'internal_notes']
        widgets = {'internal_notes': forms.Textarea(attrs={'rows': 5})}

    def clean(self):
        data = super().clean()
        if data.get('status') in ['quoted', 'accepted', 'production', 'finished', 'delivered'] and data.get('confirmed_total') is None:
            self.add_error('confirmed_total', 'Confirma un importe antes de avanzar a este estado.')
        if self.instance.pk and Order.objects.filter(quote=self.instance).exists():
            original = Quote.objects.get(pk=self.instance.pk)
            if data.get('confirmed_total') != original.confirmed_total:
                self.add_error('confirmed_total', 'Esta cotización ya tiene un pedido. Su importe confirmado se conserva.')
        return data

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status']

class CustomerForm(forms.ModelForm):
    phone = forms.CharField(label='Teléfono', max_length=40, required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and hasattr(self.instance, 'profile'):
            self.fields['phone'].initial = self.instance.profile.phone

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if email and User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Este correo ya está asociado a otra cuenta.')
        return email

class SiteForm(ManagementForm):
    class Meta:
        model = SiteConfiguration
        fields = ['name', 'logo', 'email', 'phone', 'address', 'instagram', 'whatsapp']

class OwnedInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        for form in self.forms:
            child = form.cleaned_data.get('id') if hasattr(form, 'cleaned_data') else None
            if child and getattr(child, self.fk.attname) != self.instance.pk:
                raise forms.ValidationError('Una de las filas no pertenece a este registro.')

class ProductImagesFormSet(OwnedInlineFormSet):
    def clean(self):
        super().clean()
        primary = sum(1 for form in self.forms if form.cleaned_data and not form.cleaned_data.get('DELETE') and form.cleaned_data.get('is_primary'))
        if primary > 1:
            raise forms.ValidationError('Solo una fotografía puede ser la principal.')

ProductImages = inlineformset_factory(Product, ProductImage, formset=ProductImagesFormSet,
    fields=['image', 'alt', 'order', 'is_primary'], widgets={'image': ImagePreviewInput}, extra=0, can_delete=True)
Specifications = inlineformset_factory(Product, ProductSpecification,
    formset=OwnedInlineFormSet, fields=['label', 'value', 'order'], extra=0, can_delete=True)
OptionValues = inlineformset_factory(ProductOption, ProductOptionValue,
    formset=OwnedInlineFormSet, fields=['name', 'surcharge', 'active', 'order'], extra=0, can_delete=True)
StoryImages = inlineformset_factory(PortfolioItem, PortfolioImage,
    formset=OwnedInlineFormSet, fields=['image', 'alt', 'order'], widgets={'image': ImagePreviewInput},
    labels={'image': 'Fotografía', 'alt': 'Pie de foto / texto alternativo', 'order': 'Orden'}, extra=0, can_delete=True)
