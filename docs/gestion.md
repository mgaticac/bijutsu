## Guía de administración integrada

Entra en **`/gestion/`** con tu cuenta administradora habitual. También encontrarás «Gestión» en el menú de tu usuario. El acceso `/admin/` redirige a esta misma página; la interfaz Django Admin ya no se expone. No se cambiaron tus cuentas ni contraseñas.

### Productos, fotografías y variantes

1. En **Categorías**, crea o edita nombre, enlace, fotografía, orden y estado.
2. En **Productos → Crear producto**, completa datos, precio CLP y fotografía. Guarda.
3. Usa **Fotografías → Agregar** para ampliar la galería. Especifica texto alternativo, orden y, si corresponde, una principal.
4. En **Características → Agregar**, introduce propiedades libres: altura, número de piezas, resina, base o estado del kit.
5. En la ficha guardada, abre **Agregar opción**. Escribe Tamaño, Color, Material, Escala, Versión u otra opción, y añade valores con sus recargos en el mismo formulario.
6. **Opciones y variantes** permite editar valores, precios, activación y orden posteriormente.

Las opciones obligatorias necesitan un valor activo para poder cotizar. Se selecciona un valor por opción. Las escalas no están fijadas en el código. Para Model Kits, elige ese tipo en el producto y añade las propiedades/opciones pertinentes.

Desmarcar «Activo» oculta un producto. Desactivar una categoría oculta todos sus productos. La eliminación pide confirmación; una categoría en uso debe reasignarse o desactivarse. Las cotizaciones conservan su copia histórica aunque cambie el catálogo.

La imagen de galería marcada principal tiene prioridad sobre la imagen del producto. Para cambiar esa selección entre fotos ya guardadas, desmarca la anterior, guarda y marca la nueva. Solo puede haber una principal.

### Historias del taller: blog de experiencias

En **Historias del taller → Crear historia** puedes escribir:

- Título y enlace legible (se sugiere a partir del título).
- Resumen para la tarjeta del blog.
- Historia completa: proceso, dificultades, pruebas, aprendizajes y resultado. Una línea en blanco separa párrafos.
- Portada, tecnología, categoría y fecha opcional.
- Galería con pies de foto y orden.
- Publicación, destacado y orden.

Puedes guardar un **borrador sin fotografía**. Para publicar, agrega portada y texto y marca «Publicar historia». Los borradores no aparecen en la página pública ni se pueden abrir mediante su enlace, incluso con la sesión administrativa; el texto se revisa en el editor.

La página pública `/trabajos/` es ahora el blog, con tarjetas que abren historias individuales en `/trabajos/<enlace>/`. Conserva los filtros Filamento y Resina. Las fotos de una historia se amplían en lightbox. Un artículo destacado se muestra también en el inicio. No se inventaron experiencias del negocio para rellenarlo.

Las migraciones conservan fotografías, descripciones y estados de trabajos anteriores y asignan enlaces únicos. El texto anterior pasa a funcionar como resumen; se puede completar la historia desde la gestión. El editor utiliza texto con párrafos, no HTML arbitrario ni un constructor visual de páginas.

### Cotizaciones, producción y clientes

1. En **Cotizaciones**, busca la solicitud por cliente o correo y filtra por estado.
2. Abre la ficha: muestra la configuración histórica, comentarios y descargas privadas.
3. Edita estado, importe confirmado y notas internas. Para pasar a Cotizado o estados posteriores hace falta un importe confirmado.
4. El cliente acepta o rechaza desde su cuenta. También puedes registrar su decisión en la gestión.
5. Cuando esté Aceptada, utiliza **Crear pedido**. La conversión es transaccional y no duplica pedidos.
6. En **Pedidos**, actualiza Confirmado, En cola, Imprimiendo, Postprocesado, Listo, Entregado o Cancelado.

Una vez creado el pedido, el importe confirmado se mantiene. Los estados de solicitud y producción son independientes; el cliente consulta ambos desde el detalle de su cotización. Las notas internas no se publican.

**Clientes** permite actualizar nombre, apellidos, correo, teléfono y activación de cuentas cliente. No permite convertir clientes en administradores ni editar cuentas del personal.

### Marca y contacto

**Marca y contacto** permite reemplazar el logo y completar los datos reales del negocio. Los campos vacíos no se publican. Si no hay otro logo configurado, se utiliza `static/img/bijutsu-logo.png`, la versión limpia de la imagen entregada.

### Permisos

Se requiere una cuenta activa de personal (`is_staff`) y permisos por modelo y operación. Un superusuario tiene acceso completo. Los permisos se comprueban también al guardar/eliminar filas de galerías y valores, convertir pedidos y descargar adjuntos. Las cuentas de cliente no pueden acceder a gestión.

El registro público nunca concede acceso administrativo. Para crear tu primer administrador: `python manage.py createsuperuser` usando el entorno virtual del proyecto.
