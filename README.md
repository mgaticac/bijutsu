# BIJUTSU PRINTING

Aplicación Django para un taller de impresión 3D por encargo: catálogo, configuración de productos, cotizaciones, solicitudes de archivos propios y gestión administrativa. No incluye pagos, carrito, diseño 3D ni logística.

## Estado de esta versión

- Home, catálogo con búsqueda, categorías, filtros, precios CLP, ordenamiento y paginación.
- Productos FDM/resina, Model Kits, opciones y recargos administrables, especificaciones libres, galerías y lightbox.
- Estimación dinámica consultando al servidor; validación y recálculo al guardar.
- Registro, login/logout, perfil, cambio y recuperación de contraseña.
- Solicitudes con archivos propios y seguimiento privado de cotizaciones; aceptación/rechazo del monto confirmado.
- Administración Django, dashboard restringido, portfolio y conversión de cotizaciones aceptadas en pedidos.
- SQLite, migraciones incluidas, recursos Bootstrap locales y pruebas automatizadas.

**Identidad pendiente:** no se recibió un archivo de logo. El encabezado utiliza temporalmente el nombre tipográfico. La paleta proviene de los HEX del documento, no de una extracción del logo. No se creó un símbolo alternativo. Subir la versión definitiva en Administración → Configuración del sitio. Si el original contiene “04” o “ESTILO JAPONÉS”, preparar primero su versión limpia conservando el resto del diseño.

No se inventaron datos de contacto ni fotografías. Los espacios sin fotografía están identificados. El portfolio requiere trabajos reales. Los siete productos de ejemplo están marcados como DEMO y sus precios no representan ofertas comerciales.

## Instalación en Windows / PowerShell

Requiere Python 3.13 (entorno verificado). Desde la carpeta del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

Reemplaza `DJANGO_SECRET_KEY` en `.env` con la clave generada. En desarrollo, utiliza `DJANGO_DEBUG=True`. Se eligió este nombre para evitar conflictos con variables `DEBUG` globales de otras herramientas. Las variables del proceso tienen prioridad sobre `.env`.

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

- Sitio: http://127.0.0.1:8000/
- Administración: http://127.0.0.1:8000/admin/
- Dashboard: http://127.0.0.1:8000/gestion/

En la instalación inicial realizada en este workspace ya existen `.venv`, `.env` local con clave aleatoria, base migrada y datos demo. No se generó ningún usuario administrador ni contraseña predeterminada. Ejecuta `createsuperuser` para definir tu acceso.

`seed_demo` es idempotente, no sobrescribe productos ya existentes y solo funciona con `DJANGO_DEBUG=True`. Omite este comando en una instalación real. Las categorías se guardan en la base de datos y se pueden modificar desde el administrador; no están fijadas en las vistas.

### WAMP

Este proyecto es Python/Django; no se ejecuta al abrir `http://localhost/bijutsu/` como un proyecto PHP. Usa el servidor Django indicado arriba. `.htaccess` deniega el acceso directo desde Apache a esta carpeta para proteger código, `.env`, SQLite y archivos privados. Mantén `AllowOverride` habilitado si Apache sirve el directorio padre; la alternativa recomendada al desplegar es ubicar el código fuera del document root y configurar un servidor WSGI. Nunca expongas esta carpeta completa como archivos estáticos.

## Configuración

| Variable | Uso |
| --- | --- |
| `DJANGO_DEBUG` | `True` solo en desarrollo; por defecto `False` |
| `DJANGO_SECRET_KEY` | Clave aleatoria, mínimo 32 caracteres |
| `DJANGO_ALLOWED_HOSTS` | Hosts separados por comas, sin protocolo |
| `MAX_UPLOAD_MB` | Máximo por archivo, 25 por defecto |
| `EMAIL_BACKEND` | Consola en desarrollo; SMTP para entregar correos |
| `DEFAULT_FROM_EMAIL` | Remitente real autorizado para SMTP |
| `EMAIL_HOST`, `EMAIL_PORT` | Servidor y puerto SMTP |
| `EMAIL_USE_TLS` | `True` si corresponde al servidor |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | Credenciales SMTP |

La recuperación de contraseña está implementada con los tokens de Django. En desarrollo el enlace se imprime en la terminal; no se envía un correo real hasta configurar SMTP. No se envían notificaciones comerciales automáticas de cotizaciones en este MVP.

## Guía de administración

### Categorías y productos

1. Crea una categoría, define su slug, imagen, orden y estado.
2. Crea un producto con nombre, descripciones, tecnología, tipo, precio base y fotografía principal.
3. Marca destacado/nuevo según corresponda; desmarca DEMO al publicar un producto real revisado.
4. En la misma ficha añade fotografías y propiedades como altura, piezas, resina, base o estado del kit.
5. Añade opciones —por ejemplo Tamaño, Color, Material, Escala o Versión— y guarda el producto.
6. Abre cada opción mediante su enlace de edición, o desde «Opciones de producto», para crear sus valores y recargos. Las opciones y sus valores se activan y ordenan de manera independiente.

Las opciones obligatorias deben tener al menos un valor activo para que el producto se pueda cotizar. Una opción admite un valor seleccionado por solicitud. Para combinaciones comerciales específicas, crea una opción «Versión» con los recargos correspondientes; esta versión no incluye matrices de dependencias entre opciones.

Una fotografía de galería marcada principal tiene prioridad sobre la imagen principal del producto. Solo puede existir una principal de galería por producto. Elimina esa marca antes de asignarla a otra foto.

Para Model Kits utiliza el tipo «Model Kit». Las escalas son valores administrables de una opción; la altura o cantidad de piezas se describen mediante propiedades. No se asume una escala ni un número fijo de piezas para todos los kits.

Desactivar una categoría oculta también sus productos en todas las páginas públicas. Los slugs deben ser únicos. Las categorías usadas por productos no se borran accidentalmente: primero reasigna esos productos o desactiva la categoría.

### Portfolio y marca

«Trabajos realizados» gestiona título, fotografía, galería, tecnología, categoría, fecha, descripción, destacados y orden. Publica únicamente fotografías reales propias o autorizadas; no se crean ejemplos ficticios de trabajos terminados.

«Configuración del sitio» permite subir el logo y completar nombre, correo, teléfono, dirección, Instagram y WhatsApp. Los campos vacíos no se muestran. La identidad CSS está centralizada en `static/css/variables.css`. El nombre BIJUTSU PRINTING permanece explícito en las composiciones de marca de este proyecto.

### Cotizaciones y pedidos

1. El cliente inicia sesión, configura el producto y envía sus datos, comentarios y archivos opcionales. Para archivos propios debe adjuntar un modelo.
2. La solicitud aparece como Pendiente. Cambia a En revisión y revisa los adjuntos privados.
3. Establece el total confirmado y el estado Cotizado. El cliente podrá aceptar o rechazar ese monto desde su cuenta.
4. Una vez Aceptado y con total confirmado, selecciona la cotización en la lista administrativa y ejecuta «Convertir cotizaciones aceptadas en pedidos».
5. Actualiza el estado del pedido: Confirmado, En cola, Imprimiendo, Postprocesado, Listo, Entregado o Cancelado. El cliente ve ese estado en el detalle de su cotización.

La conversión es transaccional e idempotente: una cotización solo genera un pedido. Se conserva el total confirmado y una copia de las líneas/opciones originales. El precio unitario de la línea es el estimado histórico; el total del pedido es el importe final acordado. Los estados de cotización y pedido son independientes y no se sincronizan automáticamente; el detalle muestra ambos.

Las notas internas nunca aparecen en el área del cliente. La descarga exige ser el propietario o un empleado con permiso para ver cotizaciones. Una cuenta con `is_staff` sin los permisos correspondientes no obtiene acceso a los archivos.

El dashboard requiere `is_staff` y permisos de consulta de cotizaciones, productos, usuarios y pedidos. Un superusuario tiene todos estos permisos. La conversión administrativa requiere además permiso para agregar pedidos.

## Arquitectura

```text
bijutsu_printing/       Configuración, URLs y WSGI
apps/
  core/                Configuración de marca, imágenes, home, filtro CLP y seed_demo
  catalog/             Categorías, productos, imágenes, opciones, precio y filtros
  accounts/            Registro y perfil; autenticación nativa Django
  quotes/              Solicitudes, adjuntos privados, validación, seguimiento
  orders/              Conversión transaccional y estados de producción
  portfolio/           Trabajos reales y galerías
  dashboard/           Métricas y accesos de administración
templates/             Layout, componentes y pantallas por módulo
static/css/            Variables e identidad sobre Bootstrap
static/js/             Configurador, galerías y formularios
static/vendor/         Bootstrap 5.3.8 local y su licencia MIT
scripts/               Prueba de navegador
```

`catalog/services.py` es el punto de extensión para el cálculo de precios. Los importes CLP usan `DecimalField` sin fracciones; el navegador no decide el monto guardado. Una cotización conserva instantáneas de nombre, cantidad, precio unitario y opciones, aun cuando el catálogo cambie o se elimine un producto. Los modelos utilizan relaciones y campos compatibles con PostgreSQL. Para migrar posteriormente, instala su driver, configura `DATABASES`, aplica migraciones y transfiere/verifica los datos; no se requiere rehacer los modelos.

## Archivos, imágenes y seguridad

- `media/`: imágenes públicas del catálogo, categorías, portfolio y logo.
- `media/thumbnails/`: versiones WebP de hasta 900 × 900 px; se mantienen originales para ampliación.
- `private_media/quotes/`: STL, OBJ, 3MF, ZIP y referencias del cliente. **No se publica con `MEDIA_URL`.**
- `static/`: fuentes estáticas; `staticfiles/`: resultado de `collectstatic`.
- Los nombres de archivo son UUID; no se usan nombres del cliente como rutas de almacenamiento.
- Adjuntos: hasta cinco archivos de 25 MB, límite durante recepción, validación de extensión, MIME y contenido. El ZIP admite STL/OBJ e imágenes; rechaza rutas externas, ejecutables, archivos cifrados, archivos anidados y expansiones excesivas. Un 3MF valida el contenedor y XML de modelo; no se extrae al disco.
- La validación es de formato, **no un análisis de imprimibilidad ni antivirus**. El taller revisa manualmente escala, geometría, licencias y viabilidad antes de confirmar.
- CSRF, sesiones Django, validadores de contraseña, escape de texto, vistas privadas y comprobación de propiedad en descargas.
- Los archivos no se eliminan automáticamente al borrar registros: requiere una política de retención y limpieza con respaldo. Un fallo al guardar una solicitud sí limpia los archivos que esa operación alcanzó a crear.

## Pruebas

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test
```

Cubren precios, opciones ajenas/inactivas/duplicadas, cantidades, permisos, CSRF, aislamiento de cotizaciones, uploads, capturas históricas de precios, cuentas, correo de recuperación y conversión idempotente a pedidos. Las pruebas usan una base de datos temporal y nunca requieren credenciales del administrador.

Prueba de navegador opcional, con servidor en ejecución, datos demo y Microsoft Edge instalado:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe scripts/browser_smoke.py
```

Comprueba páginas públicas, cálculo de $27.000, redirección a login, menú offcanvas y ausencia de desbordamiento a 1440 y 390 px. Guarda capturas en `test-results/`, excluido de Git. Para otros sistemas cambia `channel='msedge'` por el navegador instalado o instala Chromium con Playwright.

## Publicación

Antes de publicar: incorporar logo/fotografías reales, revisar precios, quitar o desactivar demos, completar solo los datos de contacto autorizados y configurar SMTP. Este repositorio no configura hosting, DNS ni certificados.

```powershell
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
# En el entorno de producción, con DJANGO_DEBUG=False:
.\.venv\Scripts\python.exe manage.py check --deploy
```

Usa HTTPS y un servidor WSGI de producción; no `runserver`. Con `DJANGO_DEBUG=False` se activan redirección HTTPS, cookies seguras y HSTS para el host. Configura explícitamente los hosts permitidos, respaldo de base y medios, límites del proxy y la entrega de `staticfiles` e imágenes públicas. Nunca sirvas `.env`, SQLite, código Python ni `private_media` directamente. Si hay un proxy TLS, configura la cabecera de protocolo únicamente cuando ese proxy sea confiable y elimine cabeceras entrantes falsificadas.

Mantén las dependencias actualizadas. Referencias: [versiones soportadas de Django](https://www.djangoproject.com/download/) y [seguridad de archivos subidos](https://docs.djangoproject.com/en/5.2/topics/security/#user-uploaded-content).

## Alcance futuro

Quedan fuera: pagos, carrito, promociones, inventario, costeo industrial, impresoras/mantenciones, despacho, reseñas y notificaciones WhatsApp. La separación de precios, cotizaciones y pedidos permite incorporarlos sin acoplarlos al catálogo.

La comprobaci?n de despliegue puede advertir sobre HSTS para subdominios y preload. No se habilitan autom?ticamente: dependen del dominio definitivo y de que todos sus subdominios utilicen HTTPS.
