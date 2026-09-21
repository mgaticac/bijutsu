from .models import Product

def public_products():
    return Product.objects.filter(active=True, category__active=True).select_related('category').prefetch_related('images')
