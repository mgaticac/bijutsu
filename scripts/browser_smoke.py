"""Public browser smoke test. Run with the development server and seed_demo."""
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = 'http://127.0.0.1:8000'
OUTPUT = Path('test-results')
OUTPUT.mkdir(exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(channel='msedge', headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 1000}, device_scale_factor=1)
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    for route in ['/', '/catalogo/', '/filamento/', '/resina/', '/model-kits/', '/trabajos/', '/cuenta/login/', '/cuenta/registro/']:
        response = page.goto(BASE + route)
        assert response.status == 200, (route, response.status)
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), route
    page.goto(BASE)
    page.screenshot(path=str(OUTPUT / 'home-desktop.png'), full_page=True)
    page.goto(BASE + '/producto/dragon-articulado/')
    page.get_by_label('Tamaño').select_option(label='Grande')
    page.get_by_label('Color').select_option(label='Multicolor')
    page.get_by_label('Material').select_option(label='PLA')
    page.get_by_label('Cantidad').fill('2')
    page.get_by_label('Cantidad').blur()
    page.wait_for_function("document.querySelector('[data-total]').textContent.includes('27.000')")
    page.screenshot(path=str(OUTPUT / 'product-desktop.png'), full_page=True)
    page.get_by_role('button', name='Solicitar cotización').click()
    page.wait_for_url('**/cuenta/login/**')
    assert 'csrfmiddlewaretoken' not in page.url
    page.set_viewport_size({'width': 390, 'height': 844})
    for route in ['/', '/catalogo/', '/producto/dragon-articulado/', '/trabajos/', '/cuenta/registro/']:
        page.goto(BASE + route)
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), route
    page.goto(BASE)
    page.get_by_role('button', name='Abrir menú').click()
    page.wait_for_function("document.getElementById('navigation').classList.contains('show')")
    page.get_by_role('button', name='Cerrar menú').click()
    page.wait_for_function("!document.getElementById('navigation').classList.contains('show')")
    page.screenshot(path=str(OUTPUT / 'home-mobile.png'), full_page=True)
    assert not errors, errors
    browser.close()
    print('Browser smoke passed: public pages, server pricing, login redirect, desktop/mobile and offcanvas.')
