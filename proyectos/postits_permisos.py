"""Permisos de la app ``postits`` para notas ligadas a un ``Proyecto``."""
from docs.views import _puede_ver_seccion, _sitios_permitidos


def puede_ver(user, proyecto):
    if not _puede_ver_seccion(user, "acceso_proyectos"):
        return False
    permitidos = _sitios_permitidos(user, proyecto.empresa)
    return permitidos is None or proyecto.sitio in permitidos


def etiqueta(proyecto):
    return f"{proyecto.empresa} / {proyecto.sitio}"
