from django.urls import path
from . import views
app_name = 'quotes'
urlpatterns = [
    path('solicitar-impresion/', views.create, name='custom'),
    path('cotizar/<slug:slug>/', views.create, name='create'),
    path('mis-cotizaciones/', views.quote_list, name='list'),
    path('cotizacion/<uuid:reference>/', views.detail, name='detail'),
    path('cotizacion/<uuid:reference>/responder/', views.respond, name='respond'),
    path('adjunto/<int:pk>/', views.attachment, name='attachment'),
]
