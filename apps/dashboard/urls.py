from django.urls import path
from . import views
app_name = 'management'
urlpatterns = [
    path('configuracion/', views.settings_view, name='settings'),
    path('cotizaciones/<int:pk>/crear-pedido/', views.create_order, name='convert'),
    path('<slug:section>/', views.listing, name='list'),
    path('<slug:section>/nuevo/', views.edit, name='create'),
    path('<slug:section>/<int:pk>/', views.edit, name='edit'),
    path('<slug:section>/<int:pk>/eliminar/', views.delete, name='delete'),
]
