# postits — notas post-it reutilizables

Notas adhesivas **generales** (del usuario) o **ligadas a cualquier objeto** (GenericForeignKey),
con botón flotante + panel lateral. Colores, fijar/archivar, recordatorio y checklist.
Personal por defecto; en notas de objeto se pueden **compartir** (solo lectura para los demás).

## Instalar en otro proyecto
1. Copiar la carpeta `postits/` y añadir `'postits'` a `INSTALLED_APPS` (requiere `contenttypes`).
2. `path('postits/', include('postits.urls', namespace='postits'))` y `migrate`.
3. En `base.html`: `{% load postits %}{% postits_widget %}` antes de `</body>`
   (solo se pinta con usuario autenticado). Usa FontAwesome y clases DaisyUI (`btn`, `tabs`).
4. Settings opcionales:
   - `POSTITS_MODELOS_PERMITIDOS = ['app.modelo']` — qué modelos se pueden anotar (default `[]`).
   - `POSTITS_PUEDE_VER_OBJETO = 'ruta.funcion'` — `f(user, obj) -> bool` (default: permite).
   - `POSTITS_ETIQUETA_OBJETO = 'ruta.funcion'` — `f(obj) -> str`.
5. En la página que muestra un objeto, avisar el contexto:
   `window.Postits.setContexto({tipo: 'app.modelo', id: 1, etiqueta: 'Nombre'})`
   (o `document.dispatchEvent(new CustomEvent('postits:contexto', {detail: {...}}))`; `null` lo quita).
   Con contexto aparece la pestaña del objeto junto a «Generales».

## Aquí
`proyectos.Proyecto`, permisos en `proyectos/postits_permisos.py`; `seguimiento.html` emite
`postits:contexto` al cargar un sitio. En producción, `collectstatic` (deploy) sirve el JS/CSS.
