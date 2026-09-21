from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.urls import include, path
from apps.core.views import home
from apps.accounts.views import register, profile
from apps.portfolio.views import portfolio, story
from apps.dashboard.views import dashboard

urlpatterns = [
    path('', home, name='home'),
    path('', include('apps.catalog.urls')),
    path('', include('apps.quotes.urls')),
    path('cuenta/registro/', register, name='register'),
    path('cuenta/perfil/', profile, name='profile'),
    path('cuenta/', include('django.contrib.auth.urls')),
    path('trabajos/', portfolio, name='portfolio'),
    path('trabajos/<slug:slug>/', story, name='story'),
    path('gestion/', dashboard, name='dashboard'),
    path('gestion/', include('apps.dashboard.urls')),
    path('admin/', RedirectView.as_view(pattern_name='dashboard', permanent=False)),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
