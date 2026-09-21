from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models.functions import Coalesce
from .models import PortfolioItem

def portfolio(request):
    items = PortfolioItem.objects.filter(active=True).prefetch_related('images').order_by('-date', '-created_at', '-pk')
    technology = request.GET.get('technology')
    if technology in ('fdm', 'resin'):
        items = items.filter(technology=technology)
    return render(request, 'portfolio/list.html', {'page': Paginator(items, 12).get_page(request.GET.get('page')),
        'pagination_query': f'technology={technology}' if technology in ('fdm', 'resin') else ''})

def story(request, slug):
    work = get_object_or_404(PortfolioItem.objects.filter(active=True).select_related('category').prefetch_related('images'), slug=slug)
    return render(request, 'portfolio/story.html', {'work': work,
        'related': PortfolioItem.objects.filter(active=True).exclude(pk=work.pk).order_by('-created_at')[:3]})
