from django.contrib import admin
from .models import SiteConfiguration

@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SiteConfiguration.objects.exists() and super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.site_header = 'BIJUTSU PRINTING'
admin.site.site_title = 'Administración Bijutsu'
admin.site.index_title = 'Administración del taller'
