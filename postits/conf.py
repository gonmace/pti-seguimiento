"""Puntos de extensión de la app (todos opcionales, con defaults seguros).

``POSTITS_MODELOS_PERMITIDOS``  lista de ``"app_label.model"`` que se pueden anotar. Default
                                ``[]``: solo notas generales.
``POSTITS_PUEDE_VER_OBJETO``    ruta punteada a ``callable(user, obj) -> bool``. Default: permite.
``POSTITS_ETIQUETA_OBJETO``     ruta punteada a ``callable(obj) -> str``. Default: ``str(obj)``.
"""
from django.apps import apps
from django.conf import settings
from django.utils.module_loading import import_string


def modelos_permitidos():
    return [m.lower() for m in getattr(settings, "POSTITS_MODELOS_PERMITIDOS", [])]


def resolver_objeto(tipo, pk):
    """``(content_type, obj)`` del objeto anotable, o ``None`` si el tipo no está en la
    whitelist o el objeto no existe."""
    from django.contrib.contenttypes.models import ContentType
    if not tipo or tipo.lower() not in modelos_permitidos():
        return None
    try:
        modelo = apps.get_model(tipo)
    except (LookupError, ValueError):
        return None
    try:
        obj = modelo._default_manager.filter(pk=pk).first()
    except (ValueError, TypeError):
        return None
    if obj is None:
        return None
    return ContentType.objects.get_for_model(modelo), obj


def puede_ver_objeto(user, obj):
    ruta = getattr(settings, "POSTITS_PUEDE_VER_OBJETO", None)
    return bool(import_string(ruta)(user, obj)) if ruta else True


def etiqueta_objeto(obj):
    ruta = getattr(settings, "POSTITS_ETIQUETA_OBJETO", None)
    return import_string(ruta)(obj) if ruta else str(obj)
