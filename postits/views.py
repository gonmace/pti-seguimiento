import json
from datetime import date

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from . import conf, servicios
from .models import COLORES, Postit, PostitItem

_COLORES = {c for c, _ in COLORES}


def _body(request):
    try:
        return json.loads(request.body or b"{}")
    except ValueError:
        return {}


def _err(msg, status=400):
    return JsonResponse({"error": msg}, status=status)


def _objeto(request, tipo, pk):
    """``(objeto|None, error|None)``. Sin ``tipo`` → nota general."""
    if not tipo:
        return None, None
    res = conf.resolver_objeto(tipo, pk)
    if res is None:
        return None, _err("Objeto no válido.")
    if not conf.puede_ver_objeto(request.user, res[1]):
        return None, _err("No tienes acceso a este objeto.", 403)
    return res, None


def _mia(request, pk):
    return Postit.objects.filter(pk=pk, autor=request.user).first()


def _fecha(valor):
    if not valor:
        return None
    try:
        return date.fromisoformat(valor)
    except (TypeError, ValueError):
        raise ValueError("Fecha inválida.")


def _aplicar(p, d):
    """Copia a ``p`` los campos presentes en ``d``. Devuelve mensaje de error o None."""
    if "texto" in d:
        p.texto = str(d["texto"])[:5000]
    if "color" in d:
        if d["color"] not in _COLORES:
            return "Color inválido."
        p.color = d["color"]
    for campo in ("compartida", "fijada", "archivada"):
        if campo in d:
            setattr(p, campo, bool(d[campo]))
    if "recordatorio" in d:
        try:
            p.recordatorio = _fecha(d["recordatorio"])
        except ValueError as e:
            return str(e)
    return None


@login_required
@require_GET
def api_listar(request):
    objeto, err = _objeto(request, request.GET.get("tipo"), request.GET.get("id"))
    if err:
        return err
    qs = servicios.listar(request.user, objeto, request.GET.get("archivadas") == "1")
    return JsonResponse({"postits": [servicios.serializar(p, request.user) for p in qs]})


@login_required
@require_GET
def api_resumen(request):
    return JsonResponse(servicios.resumen(request.user))


@login_required
@require_POST
def api_crear(request):
    d = _body(request)
    objeto, err = _objeto(request, d.get("tipo"), d.get("id"))
    if err:
        return err
    p = Postit(autor=request.user)
    if objeto:
        p.content_type, p.object_id = objeto[0], str(objeto[1].pk)
    msg = _aplicar(p, d)
    if msg:
        return _err(msg)
    p.save()
    return JsonResponse({"ok": True, "postit": servicios.serializar(p, request.user)})


@login_required
@require_POST
def api_editar(request, pk):
    p = _mia(request, pk)
    if not p:
        return _err("Nota no encontrada.", 404)
    msg = _aplicar(p, _body(request))
    if msg:
        return _err(msg)
    p.save()
    return JsonResponse({"ok": True, "postit": servicios.serializar(p, request.user)})


@login_required
@require_POST
def api_borrar(request, pk):
    p = _mia(request, pk)
    if not p:
        return _err("Nota no encontrada.", 404)
    p.delete()
    return JsonResponse({"ok": True})


@login_required
@require_POST
def api_reordenar(request):
    ids = _body(request).get("ids") or []
    for orden, pk in enumerate(ids):
        Postit.objects.filter(pk=pk, autor=request.user).update(orden=orden)
    return JsonResponse({"ok": True})


@login_required
@require_POST
def api_item_crear(request, pk):
    p = _mia(request, pk)
    if not p:
        return _err("Nota no encontrada.", 404)
    texto = str(_body(request).get("texto", "")).strip()[:255]
    if not texto:
        return _err("Texto vacío.")
    i = PostitItem.objects.create(postit=p, texto=texto, orden=p.items.count())
    return JsonResponse({"ok": True, "item": {"id": i.pk, "texto": i.texto, "hecho": i.hecho}})


def _item_mio(request, pk):
    return PostitItem.objects.filter(pk=pk, postit__autor=request.user).first()


@login_required
@require_POST
def api_item_editar(request, pk):
    i = _item_mio(request, pk)
    if not i:
        return _err("Ítem no encontrado.", 404)
    d = _body(request)
    if "texto" in d:
        texto = str(d["texto"]).strip()[:255]
        if not texto:
            return _err("Texto vacío.")
        i.texto = texto
    if "hecho" in d:
        i.hecho = bool(d["hecho"])
    i.save()
    return JsonResponse({"ok": True, "item": {"id": i.pk, "texto": i.texto, "hecho": i.hecho}})


@login_required
@require_POST
def api_item_borrar(request, pk):
    i = _item_mio(request, pk)
    if not i:
        return _err("Ítem no encontrado.", 404)
    i.delete()
    return JsonResponse({"ok": True})
