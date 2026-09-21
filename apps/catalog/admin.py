from django.contrib import admin
from .models import Category, Product, ProductImage, ProductOption, ProductOptionValue, ProductSpecification

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'active', 'order']
    list_editable = ['active', 'order']
    search_fields = ['name']
    prepopulated_fields = {'slug': ['name']}

class ImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0

class SpecificationInline(admin.TabularInline):
    model = ProductSpecification
    extra = 0

class OptionInline(admin.TabularInline):
    model = ProductOption
    extra = 0
    show_change_link = True

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'technology', 'base_price', 'active', 'featured', 'is_demo']
    list_editable = ['base_price', 'active', 'featured']
    list_filter = ['technology', 'kind', 'active', 'featured', 'is_demo', 'category']
    search_fields = ['name', 'sku']
    prepopulated_fields = {'slug': ['name']}
    autocomplete_fields = ['category']
    inlines = [ImageInline, SpecificationInline, OptionInline]
    fieldsets = [
        ('Producto', {'fields': ['name', 'slug', 'category', 'technology', 'kind', 'short_description', 'description', 'image']}),
        ('Publicación y precio', {'fields': ['base_price', 'active', 'featured', 'is_new', 'is_demo', 'order', 'lead_time']}),
        ('Interno / SEO', {'classes': ['collapse'], 'fields': ['sku', 'internal_notes', 'meta_title', 'meta_description']}),
    ]

class ValueInline(admin.TabularInline):
    model = ProductOptionValue
    extra = 0

@admin.register(ProductOption)
class OptionAdmin(admin.ModelAdmin):
    list_display = ['name', 'product', 'required', 'active']
    list_filter = ['active', 'required']
    search_fields = ['name', 'product__name']
    autocomplete_fields = ['product']
    inlines = [ValueInline]

@admin.register(ProductOptionValue)
class ValueAdmin(admin.ModelAdmin):
    list_display = ['name', 'option', 'surcharge', 'active', 'order']
    list_editable = ['surcharge', 'active', 'order']
    search_fields = ['name', 'option__product__name']
    autocomplete_fields = ['option']
