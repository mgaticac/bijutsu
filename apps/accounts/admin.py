from django.contrib import admin
from .models import CustomerProfile

@admin.register(CustomerProfile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone']
    search_fields = ['user__username', 'user__email', 'phone']
    autocomplete_fields = ['user']
