from django.shortcuts import render
from apps.catalog.selectors import public_products
from apps.catalog.models import Category
from apps.portfolio.models import PortfolioItem

def home(request):
    products = public_products()
    return render(request, 'core/home.html', {
        'featured': products.filter(featured=True)[:4],
        'fdm_products': products.filter(technology='fdm')[:4],
        'kits': products.filter(kind='kit')[:4],
        'categories': Category.objects.filter(active=True)[:8],
        'works': PortfolioItem.objects.filter(active=True, featured=True)[:3],
    })
