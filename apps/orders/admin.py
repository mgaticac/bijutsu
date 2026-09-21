from django.contrib import admin
from .models import Order, OrderItem

class ItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['name', 'quantity', 'unit_estimate', 'configuration']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'status', 'total', 'created_at']
    list_filter = ['status']
    search_fields = ['quote__name', 'quote__email']
    readonly_fields = ['quote', 'total', 'created_at']
    inlines = [ItemInline]

    def has_add_permission(self, request):
        return False
