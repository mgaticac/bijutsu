from decimal import Decimal, InvalidOperation
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST
from .forms import ConfigurationForm
from .models import Category
from .selectors import public_products

def catalog(request, technology=None, category_slug=None, kits=False):
    products = public_products()
    selected_category = None
    title = 'Catálogo'
    if technology:
        title = 'Filamento' if technology == 'fdm' else 'Resina'
    technology = technology or request.GET.get('technology')
    if technology in ('fdm', 'resin'):
        products = products.filter(technology=technology)
    if kits:
        products = products.filter(kind='kit')
        title = 'Model Kits'
    category_slug = category_slug or request.GET.get('category')
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug, active=True)
        products = products.filter(category=selected_category)
        title = selected_category.name
    query = request.GET.get('q', '').strip()[:120]
    if query:
        products = products.filter(Q(name__icontains=query) | Q(short_description__icontains=query))
    for key, lookup in [('min_price', 'base_price__gte'), ('max_price', 'base_price__lte')]:
        try:
            price = Decimal(request.GET.get(key, ''))
            if price.is_finite() and 0 <= price <= 999999999999:
                products = products.filter(**{lookup: price})
        except InvalidOperation:
            pass
    if request.GET.get('featured'):
        products = products.filter(featured=True)
    if request.GET.get('new'):
        products = products.filter(is_new=True)
    ordering = {'price': 'base_price', '-price': '-base_price', 'new': '-created_at', 'name': 'name'}
    products = products.order_by(ordering.get(request.GET.get('sort'), 'order'), 'pk')
    page = Paginator(products, 12).get_page(request.GET.get('page'))
    params = request.GET.copy()
    params.pop('page', None)
    return render(request, 'catalog/list.html', {'page': page, 'title': title, 'query': query,
        'categories': Category.objects.filter(active=True), 'selected_category': selected_category,
        'technology': technology, 'pagination_query': params.urlencode()})

def product(request, slug):
    item = get_object_or_404(public_products(), slug=slug)
    return render(request, 'catalog/product.html', {'product': item, 'configuration': ConfigurationForm(product=item)})

@require_POST
def estimate_price(request, slug):
    item = get_object_or_404(public_products(), slug=slug)
    form = ConfigurationForm(request.POST, product=item)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors.get_json_data()}, status=400)
    result = form.cleaned_data['estimate']
    return JsonResponse({'unit': str(result.unit), 'total': str(result.total), 'quantity': result.quantity})
