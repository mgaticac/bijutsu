from django.urls import path
from . import views
app_name = 'catalog'
urlpatterns = [
    path('catalogo/', views.catalog, name='list'),
    path('filamento/', views.catalog, {'technology': 'fdm'}, name='fdm'),
    path('resina/', views.catalog, {'technology': 'resin'}, name='resin'),
    path('model-kits/', views.catalog, {'kits': True}, name='kits'),
    path('categoria/<slug:category_slug>/', views.catalog, name='category'),
    path('producto/<slug:slug>/', views.product, name='product'),
    path('producto/<slug:slug>/estimar/', views.estimate_price, name='estimate'),
]
