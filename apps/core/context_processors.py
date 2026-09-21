from .models import SiteConfiguration
from apps.catalog.models import Category

def site(request):
    return {'site_config': SiteConfiguration.objects.first(),
            'nav_categories': Category.objects.filter(active=True)[:8]}
