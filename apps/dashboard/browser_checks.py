"""Optional browser checks: manage.py test apps.dashboard.browser_checks."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import tempfile
from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings
from django.db.models import Count
from playwright.sync_api import sync_playwright
from apps.portfolio.models import PortfolioItem

class ManagementBrowserTests(StaticLiveServerTestCase):
    def test_blog_editor_and_responsive_management(self):
        User.objects.create_superuser('browser-owner', 'owner@example.test', 'OnlyForBrowserTests!782')
        output = Path('test-results')
        output.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media), ThreadPoolExecutor(max_workers=1) as database, sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel='msedge', headless=True)
            page = browser.new_page(viewport={'width': 1440, 'height': 1000})
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(self.live_server_url + '/cuenta/login/?next=/gestion/')
            page.locator('[name=username]').fill('browser-owner')
            page.locator('[name=password]').fill('OnlyForBrowserTests!782')
            page.get_by_role('button', name='Ingresar').click()
            page.wait_for_url('**/gestion/')
            page.screenshot(path=str(output / 'management-desktop.png'), full_page=True)
            self.assertEqual(page.locator('a[href^="/admin/"]').count(), 0)
            page.goto(self.live_server_url + '/gestion/historias/nuevo/')
            page.locator('[name=title]').fill('Historia de prueba del editor')
            page.locator('textarea[name=description]').fill('Resumen de prueba, no se publica en la base real.')
            page.locator('[name=body]').fill('Primera etapa de la impresión.\n\nSegunda etapa y aprendizajes.')
            page.locator('[name=technology]').select_option('fdm')
            page.locator('[name=image]').set_input_files('static/img/bijutsu-logo.png')
            page.locator('[data-add-form]').click()
            page.locator('[name=gallery-0-image]').set_input_files('static/img/bijutsu-logo.png')
            page.locator('[name=gallery-0-alt]').fill('Imagen de prueba del editor')
            page.get_by_role('button', name='Guardar cambios').click()
            page.wait_for_url('**/gestion/historias/*/')
            page.get_by_text('Registro creado correctamente.', exact=True).wait_for()
            story = database.submit(lambda: PortfolioItem.objects.annotate(image_count=Count('images')).get()).result()
            self.assertFalse(story.active)
            self.assertEqual(story.image_count, 1)
            self.assertEqual(page.request.get(self.live_server_url + story.get_absolute_url()).status, 404)
            page.locator('[name=active]').check()
            page.get_by_role('button', name='Guardar cambios').click()
            page.get_by_text('Cambios guardados.', exact=True).wait_for()
            page.screenshot(path=str(output / 'story-editor-desktop.png'), full_page=True)
            page.get_by_role('link', name='Ver historia').click()
            page.get_by_text('Segunda etapa y aprendizajes.', exact=True).wait_for()
            page.screenshot(path=str(output / 'story-desktop.png'), full_page=True)
            # Media are optimized/validated in unit tests. Static live server deliberately
            # uses DEBUG=False, so this test focuses on editor behavior and navigation.
            for width in [1280, 1024, 768, 390, 320]:
                page.set_viewport_size({'width': width, 'height': 844})
                for route in ['/gestion/', '/gestion/productos/', '/gestion/historias/nuevo/', '/trabajos/']:
                    page.goto(self.live_server_url + route)
                    self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (width, route))
            page.goto(self.live_server_url + '/gestion/')
            page.screenshot(path=str(output / 'management-mobile.png'), full_page=True)
            page.goto(self.live_server_url + f'/gestion/historias/{story.pk}/eliminar/')
            page.get_by_role('button', name='Sí, eliminar').click()
            page.wait_for_url('**/gestion/historias/')
            self.assertFalse(database.submit(lambda: PortfolioItem.objects.exists()).result())
            self.assertFalse(errors, errors)
            browser.close()
