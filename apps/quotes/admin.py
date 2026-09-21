from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.html import format_html
from apps.orders.services import convert_quote
from .models import Quote, QuoteItem, QuoteAttachment

class ItemInline(admin.TabularInline):
    model = QuoteItem
    fields = ['product_name', 'quantity', 'unit_price', 'configuration']
    readonly_fields = fields
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description='Opciones')
    def configuration(self, obj):
        return ' / '.join(f'{o.name}: {o.value}' for o in obj.options.all())

class AttachmentInline(admin.TabularInline):
    model = QuoteAttachment
    fields = ['original_name', 'download']
    readonly_fields = fields
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def download(self, obj):
        return format_html('<a href="{}">Descargar</a>', reverse('quotes:attachment', args=[obj.pk]))

@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'name', 'status', 'estimated_total', 'confirmed_total', 'created_at']
    list_filter = ['status', 'technology', 'created_at']
    search_fields = ['name', 'email', 'customer__username']
    autocomplete_fields = ['customer']
    readonly_fields = ['reference', 'estimated_total', 'created_at', 'updated_at']
    inlines = [ItemInline, AttachmentInline]
    actions = ['create_orders']

    @admin.action(description='Convertir cotizaciones aceptadas en pedidos')
    def create_orders(self, request, queryset):
        if not request.user.has_perm('orders.add_order'):
            self.message_user(request, 'No tienes permiso para crear pedidos.', messages.ERROR)
            return
        for quote in queryset:
            try:
                order = convert_quote(quote)
                self.message_user(request, str(order), messages.SUCCESS)
            except ValidationError as error:
                self.message_user(request, f'{quote}: {error.messages[0]}', messages.ERROR)
