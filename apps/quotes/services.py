from pathlib import Path
from django.db import transaction
from .models import QuoteItem, QuoteItemOption, QuoteAttachment

def create_quote(*, customer, form, product=None, configuration=None):
    stored = []
    try:
        with transaction.atomic():
            quote = form.save(commit=False)
            quote.customer = customer
            if product:
                from apps.catalog.services import estimate
                # Resolve live prices again at persistence time.
                result = estimate(product, configuration.quantity, [v.pk for v in configuration.values])
                quote.estimated_total = result.total
                quote.quantity = result.quantity
                quote.technology = product.technology
            quote.save()
            if product:
                item = QuoteItem.objects.create(quote=quote, product=product, product_name=product.name,
                    quantity=result.quantity, unit_price=result.unit)
                QuoteItemOption.objects.bulk_create([QuoteItemOption(item=item, name=v.option.name, value=v.name, surcharge=v.surcharge) for v in result.values])
            for file in form.cleaned_data['attachments']:
                attachment = QuoteAttachment(quote=quote, file=file, original_name=Path(file.name).name)
                attachment.save()
                stored.append(attachment.file)
            return quote
    except Exception:
        for file in stored:
            file.delete(save=False)
        raise
