from django.contrib import admin
from .models import PortfolioItem, PortfolioImage

class ImageInline(admin.TabularInline):
    model = PortfolioImage
    extra = 0

@admin.register(PortfolioItem)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ['title', 'technology', 'active', 'featured', 'order']
    list_editable = ['active', 'featured', 'order']
    search_fields = ['title']
    list_filter = ['technology', 'featured', 'active']
    autocomplete_fields = ['category']
    inlines = [ImageInline]
