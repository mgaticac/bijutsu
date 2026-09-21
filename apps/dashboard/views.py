from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from apps.accounts.models import CustomerProfile
from apps.catalog.models import Product, ProductOption
from apps.core.models import SiteConfiguration
from apps.orders.models import Order
from apps.orders.services import convert_quote
from apps.portfolio.models import PortfolioItem
from apps.quotes.models import Quote
from .forms import ProductImages, Specifications, OptionValues, StoryImages, SiteForm
from .permissions import staff_only, require_model_permission
from .registry import SECTIONS, management_navigation

def context(request, **kwargs):
    return {'management_nav': management_navigation(request.user), **kwargs}

def section_for(key):
    if key not in SECTIONS:
        raise Http404
    return SECTIONS[key]

def queryset_for(section):
    query = section.model.objects.all()
    if section.model is User:
        return query.filter(is_staff=False, is_superuser=False).select_related('profile').order_by('username')
    return query

@staff_only
def dashboard(request):
    if not request.user.has_perms(['quotes.view_quote', 'catalog.view_product', 'auth.view_user', 'orders.view_order']):
        navigation = management_navigation(request.user)
        if navigation:
            return redirect('management:list', section=navigation[0]['key'])
        raise PermissionDenied
    metrics = [(label, Quote.objects.filter(status=value).count()) for value, label in Quote.Status.choices if value in ('pending', 'review', 'accepted')]
    metrics.extend([
        ('En producción', Order.objects.filter(status__in=['printing', 'finishing']).count()),
        ('Trabajos listos', Order.objects.filter(status='ready').count()),
        ('Clientes', User.objects.filter(is_staff=False).count()),
        ('Productos activos', Product.objects.filter(active=True, category__active=True).count()),
    ])
    return render(request, 'dashboard/index.html', context(request, metrics=metrics, quotes=Quote.objects.all()[:8], active_section='overview'))

@staff_only
def listing(request, section):
    config = section_for(section)
    require_model_permission(request.user, config.model, 'view')
    items = queryset_for(config)
    query = request.GET.get('q', '').strip()[:120]
    if query:
        condition = Q()
        for field in config.search:
            condition |= Q(**{f'{field}__icontains': query})
        items = items.filter(condition)
    product = None
    if section == 'opciones':
        items = items.select_related('product')
        if request.GET.get('product', '').isdigit():
            product = get_object_or_404(Product, pk=request.GET['product'])
            items = items.filter(product=product)
    if section == 'productos':
        items = items.select_related('category')
    if section == 'pedidos':
        items = items.select_related('quote')
    if section == 'historias' and request.GET.get('state') in ('draft', 'published'):
        items = items.filter(active=request.GET['state'] == 'published')
    if section in ('cotizaciones', 'pedidos') and request.GET.get('state'):
        items = items.filter(status=request.GET['state'])
    page = Paginator(items, 15).get_page(request.GET.get('page'))
    params = request.GET.copy()
    params.pop('page', None)
    opts = config.model._meta
    return render(request, 'dashboard/list.html', context(request, config=config, section=section, active_section=section,
        page=page, query=query, product=product, pagination_query=params.urlencode(),
        can_create=config.create and request.user.has_perm(f'{opts.app_label}.add_{opts.model_name}'),
        states=config.model.Status.choices if section in ('cotizaciones', 'pedidos') else []))

def build_formsets(request, instance):
    factories = []
    if isinstance(instance, Product):
        factories = [('Fotografías', 'images', ProductImages), ('Características', 'specs', Specifications)]
    elif isinstance(instance, ProductOption):
        factories = [('Valores y recargos', 'values', OptionValues)]
    elif isinstance(instance, PortfolioItem):
        factories = [('Galería de la historia', 'gallery', StoryImages)]
    result = []
    for title, prefix, factory in factories:
        opts = factory.model._meta
        if request.user.has_perm(f'{opts.app_label}.view_{opts.model_name}'):
            formset = factory(request.POST if request.method == 'POST' else None, request.FILES or None, instance=instance, prefix=prefix)
            result.append({'title': title, 'prefix': prefix, 'formset': formset,
                'can_add': request.user.has_perm(f'{opts.app_label}.add_{opts.model_name}')})
    return result

def check_formset_permissions(user, formsets):
    for group in formsets:
        formset = group['formset']
        for form in formset.forms:
            if not form.cleaned_data:
                continue
            if form.cleaned_data.get('DELETE') and form.instance.pk:
                require_model_permission(user, formset.model, 'delete')
            elif form.has_changed() and not form.cleaned_data.get('DELETE'):
                require_model_permission(user, formset.model, 'change' if form.instance.pk else 'add')

@staff_only
def edit(request, section, pk=None):
    config = section_for(section)
    if pk is None and not config.create:
        raise Http404
    require_model_permission(request.user, config.model, 'view')
    require_model_permission(request.user, config.model, 'change' if pk else 'add')
    instance = get_object_or_404(queryset_for(config), pk=pk) if pk else config.model()
    initial = {}
    if section == 'opciones' and not pk and request.GET.get('product', '').isdigit():
        initial['product'] = get_object_or_404(Product, pk=request.GET['product'])
    form = config.form(request.POST if request.method == 'POST' else None, request.FILES or None, instance=instance, initial=initial)
    formsets = build_formsets(request, instance)
    if request.method == 'POST':
        valid = form.is_valid()
        for group in formsets:
            valid = group['formset'].is_valid() and valid
        if valid:
            check_formset_permissions(request.user, formsets)
            with transaction.atomic():
                instance = form.save()
                for group in formsets:
                    group['formset'].instance = instance
                    group['formset'].save()
                if section == 'clientes':
                    CustomerProfile.objects.update_or_create(user=instance, defaults={'phone': form.cleaned_data['phone']})
            messages.success(request, 'Cambios guardados.' if pk else 'Registro creado correctamente.')
            return redirect('management:edit', section=section, pk=instance.pk)
    opts = config.model._meta
    return render(request, 'dashboard/edit.html', context(request, config=config, section=section, active_section=section,
        object=instance, form=form, formsets=formsets,
        can_delete=bool(pk and config.delete and request.user.has_perm(f'{opts.app_label}.delete_{opts.model_name}')),
        can_convert=section == 'cotizaciones' and request.user.has_perm('orders.add_order') and instance.status == 'accepted' and instance.confirmed_total is not None))

@staff_only
def delete(request, section, pk):
    config = section_for(section)
    if not config.delete:
        raise Http404
    require_model_permission(request.user, config.model, 'view')
    require_model_permission(request.user, config.model, 'delete')
    instance = get_object_or_404(queryset_for(config), pk=pk)
    if request.method == 'POST':
        try:
            with transaction.atomic():
                instance.delete()
            messages.success(request, 'Registro eliminado.')
            return redirect('management:list', section=section)
        except ProtectedError:
            messages.error(request, 'Este registro está en uso. Reasigna los elementos relacionados o desactívalo.')
    return render(request, 'dashboard/delete.html', context(request, config=config, section=section, active_section=section, object=instance))

@staff_only
@require_POST
def create_order(request, pk):
    require_model_permission(request.user, Quote, 'change')
    require_model_permission(request.user, Quote, 'view')
    require_model_permission(request.user, Order, 'add')
    quote = get_object_or_404(Quote, pk=pk)
    try:
        order = convert_quote(quote)
        messages.success(request, f'Pedido #{order.pk} confirmado. Puedes continuar con la producción.')
    except ValidationError as error:
        messages.error(request, error.messages[0])
    return redirect('management:edit', section='cotizaciones', pk=pk)

@staff_only
def settings_view(request):
    require_model_permission(request.user, SiteConfiguration, 'view')
    require_model_permission(request.user, SiteConfiguration, 'change')
    instance = SiteConfiguration.objects.first() or SiteConfiguration(pk=1)
    form = SiteForm(request.POST if request.method == 'POST' else None, request.FILES or None, instance=instance)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Configuración actualizada.')
        return redirect('management:settings')
    return render(request, 'dashboard/settings.html', context(request, form=form, active_section='settings'))
