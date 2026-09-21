from django.db import migrations, models
from django.utils import timezone
from django.utils.text import slugify

def assign_slugs(apps, schema_editor):
    Item = apps.get_model('portfolio', 'PortfolioItem')
    for item in Item.objects.all():
        item.slug = f'{slugify(item.title)[:160] or "historia"}-{item.pk}'
        item.save(update_fields=['slug'])

class Migration(migrations.Migration):
    dependencies = [('portfolio', '0001_initial')]
    operations = [
        migrations.AddField(model_name='portfolioitem', name='slug', field=models.SlugField(default='', max_length=180, verbose_name='enlace de la historia'), preserve_default=False),
        migrations.AddField(model_name='portfolioitem', name='body', field=models.TextField(blank=True, verbose_name='historia y experiencia', help_text='Cuenta el proceso, las pruebas, dificultades y lo que aprendiste. Separa los párrafos con una línea en blanco.')),
        migrations.AddField(model_name='portfolioitem', name='created_at', field=models.DateTimeField(auto_now_add=True, default=timezone.now), preserve_default=False),
        migrations.AddField(model_name='portfolioitem', name='updated_at', field=models.DateTimeField(auto_now=True)),
        migrations.AlterField(model_name='portfolioitem', name='description', field=models.TextField(blank=True, verbose_name='resumen')),
        migrations.AlterField(model_name='portfolioitem', name='active', field=models.BooleanField(default=False, verbose_name='publicada')),
        migrations.RunPython(assign_slugs, migrations.RunPython.noop),
        migrations.AlterField(model_name='portfolioitem', name='slug', field=models.SlugField(unique=True, max_length=180, verbose_name='enlace de la historia')),
    ]
