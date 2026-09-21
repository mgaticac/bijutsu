from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from apps.catalog.forms import ConfigurationForm
from apps.catalog.selectors import public_products
from .forms import QuoteForm, CustomPrintForm
from .models import Quote, QuoteAttachment
from .services import create_quote

@login_required
def create(request, slug=None):
    product = get_object_or_404(public_products(), slug=slug) if slug else None
    initial = {'name': request.user.get_full_name(), 'email': request.user.email}
    if hasattr(request.user, 'profile'):
        initial['phone'] = request.user.profile.phone
    form_class = QuoteForm if product else CustomPrintForm
    form = form_class(request.POST or None, request.FILES or None, initial=initial)
    configuration = ConfigurationForm(request.POST if request.method == 'POST' else request.GET or None, product=product) if product else None
    if request.method == 'POST':
        valid = form.is_valid()
        config_valid = configuration.is_valid() if configuration else True
        if valid and config_valid:
            try:
                quote = create_quote(customer=request.user, form=form, product=product,
                    configuration=configuration.cleaned_data['estimate'] if configuration else None)
                messages.success(request, 'Solicitud recibida. Revisaremos los detalles para confirmar el precio.')
                return redirect('quotes:detail', reference=quote.reference)
            except ValidationError as exc:
                form.add_error(None, exc)
    return render(request, 'quotes/create.html', {'form': form, 'configuration': configuration, 'product': product})

@login_required
def quote_list(request):
    quotes = Quote.objects.filter(customer=request.user).prefetch_related('items')
    return render(request, 'quotes/list.html', {'page': Paginator(quotes, 15).get_page(request.GET.get('page'))})

@login_required
def detail(request, reference):
    quote = get_object_or_404(Quote.objects.filter(customer=request.user).prefetch_related('items__options', 'attachments'), reference=reference)
    return render(request, 'quotes/detail.html', {'quote': quote})

@login_required
@require_POST
def respond(request, reference):
    from django.db import transaction
    with transaction.atomic():
        quote = get_object_or_404(Quote.objects.select_for_update(), reference=reference, customer=request.user)
        decision = request.POST.get('decision')
        if quote.status == Quote.Status.QUOTED and quote.confirmed_total is not None and decision in ('accepted', 'rejected'):
            quote.status = decision
            quote.save(update_fields=['status', 'updated_at'])
            messages.success(request, 'Tu respuesta quedó registrada.')
        else:
            messages.error(request, 'Esta cotización no admite esa respuesta.')
    return redirect('quotes:detail', reference=reference)

@login_required
def attachment(request, pk):
    files = QuoteAttachment.objects.select_related('quote')
    if not (request.user.is_staff and request.user.has_perm('quotes.view_quote')):
        files = files.filter(quote__customer=request.user)
    file = get_object_or_404(files, pk=pk)
    try:
        response = FileResponse(file.file.open('rb'), as_attachment=True, filename=file.original_name, content_type='application/octet-stream')
    except FileNotFoundError:
        raise Http404('Archivo no disponible')
    response['X-Content-Type-Options'] = 'nosniff'
    response['Cache-Control'] = 'private, no-store'
    return response
