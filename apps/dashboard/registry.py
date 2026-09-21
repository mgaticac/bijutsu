"""Explicit list of supported management screens; never resolve arbitrary model names."""
from dataclasses import dataclass
from django.contrib.auth.models import User
from apps.catalog.models import Product, Category, ProductOption
from apps.portfolio.models import PortfolioItem
from apps.quotes.models import Quote
from apps.orders.models import Order
from .forms import ProductForm, CategoryForm, OptionForm, StoryForm, QuoteManagementForm, OrderForm, CustomerForm

@dataclass(frozen=True)
class Section:
    title: str
    singular: str
    model: type
    form: type
    search: tuple
    create: bool = True
    delete: bool = True

SECTIONS = {
    'productos': Section('Productos', 'producto', Product, ProductForm, ('name', 'sku')),
    'categorias': Section('Categorías', 'categoría', Category, CategoryForm, ('name',)),
    'opciones': Section('Opciones y variantes', 'opción', ProductOption, OptionForm, ('name', 'product__name')),
    'historias': Section('Historias del taller', 'historia', PortfolioItem, StoryForm, ('title', 'description', 'body')),
    'cotizaciones': Section('Cotizaciones', 'cotización', Quote, QuoteManagementForm, ('name', 'email'), create=False, delete=False),
    'pedidos': Section('Pedidos', 'pedido', Order, OrderForm, ('quote__name', 'quote__email'), create=False, delete=False),
    'clientes': Section('Clientes', 'cliente', User, CustomerForm, ('username', 'email', 'first_name', 'last_name'), create=False, delete=False),
}

def management_navigation(user):
    return [{'key': key, 'title': section.title} for key, section in SECTIONS.items()
            if user.has_perm(f'{section.model._meta.app_label}.view_{section.model._meta.model_name}')]
