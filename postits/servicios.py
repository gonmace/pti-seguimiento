from django.db.models import Q

from . import conf
from .models import Postit


def nombre_usuario(u):
    return (u.get_full_name() or u.email or u.username) if u else ""


def serializar(p, user):
    return {
        "id": p.pk, "titulo": p.titulo, "texto": p.texto, "color": p.color,
        "compartida": p.compartida, "fijada": p.fijada, "archivada": p.archivada,
        "recordatorio": p.recordatorio.isoformat() if p.recordatorio else "",
        "vencida": p.vencida, "es_mio": p.autor_id == user.pk,
        "autor": nombre_usuario(p.autor),
        "items": [{"id": i.pk, "texto": i.texto, "hecho": i.hecho} for i in p.items.all()],
    }


def listar(user, objeto=None, archivadas=False):
    """Notas generales del usuario (``objeto=None``) o las del objeto: las propias más las
    compartidas por otros."""
    qs = Postit.objects.select_related("autor").prefetch_related("items")
    if objeto is None:
        qs = qs.filter(autor=user, content_type__isnull=True)
    else:
        ct, obj = objeto
        qs = qs.filter(content_type=ct, object_id=str(obj.pk)).filter(
            Q(autor=user) | Q(compartida=True))
    return qs.filter(archivada=archivadas)


def resumen(user):
    """Conteos para el badge del FAB (notas generales activas del usuario)."""
    qs = Postit.objects.filter(autor=user, content_type__isnull=True, archivada=False)
    return {"activas": qs.count(), "vencidas": sum(1 for p in qs if p.vencida)}
