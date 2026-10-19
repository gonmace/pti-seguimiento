import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.template import Context, Template
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from docs.models import AccesoSitio, UserProfile
from proyectos import servicios

from .models import Postit

User = get_user_model()


class PostitsBase(TestCase):
    def setUp(self):
        cache.clear()
        self.u = User.objects.create_user("a@x.cl", "a@x.cl", "pw")
        self.o = User.objects.create_user("b@x.cl", "b@x.cl", "pw")
        for u in (self.u, self.o):
            UserProfile.objects.update_or_create(
                user=u, defaults={"rol": "rol_ito", "acceso_proyectos": True})
        self.proy = servicios.obtener_proyecto("AJ", "S1")
        AccesoSitio.objects.create(user=self.u, empresa="AJ", sitio="S1")
        self.client.force_login(self.u)

    def post(self, name, body=None, args=None, client=None):
        return (client or self.client).post(
            reverse(f"postits:{name}", args=args or []),
            data=json.dumps(body or {}), content_type="application/json")

    def listar(self, client=None, **q):
        return (client or self.client).get(reverse("postits:listar"), q)

    def otro(self):
        c = self.client_class()
        c.force_login(self.o)
        return c


class GeneralesTests(PostitsBase):
    def test_crear_y_listar_solo_propias(self):
        r = self.post("crear", {"texto": "hola", "color": "rosa"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(self.listar().json()["postits"]), 1)
        self.assertEqual(self.listar(self.otro()).json()["postits"], [])

    def test_otro_no_edita_ni_borra(self):
        pk = self.post("crear", {"texto": "x"}).json()["postit"]["id"]
        c = self.otro()
        self.assertEqual(self.post("editar", {"texto": "y"}, [pk], c).status_code, 404)
        self.assertEqual(self.post("borrar", {}, [pk], c).status_code, 404)
        self.assertTrue(Postit.objects.filter(pk=pk, texto="x").exists())

    def test_color_invalido(self):
        self.assertEqual(self.post("crear", {"color": "negro"}).status_code, 400)

    def test_archivar_fijar_y_filtro(self):
        pk = self.post("crear", {"texto": "x"}).json()["postit"]["id"]
        self.post("editar", {"fijada": True, "archivada": True}, [pk])
        self.assertEqual(self.listar().json()["postits"], [])
        self.assertEqual(len(self.listar(archivadas=1).json()["postits"]), 1)

    def test_vencida_y_resumen(self):
        ayer = (timezone.localdate() - timedelta(days=1)).isoformat()
        self.post("crear", {"texto": "x", "recordatorio": ayer})
        self.post("crear", {"texto": "y"})
        r = self.client.get(reverse("postits:resumen")).json()
        self.assertEqual(r, {"activas": 2, "vencidas": 1})

    def test_checklist(self):
        pk = self.post("crear", {}).json()["postit"]["id"]
        i = self.post("item_crear", {"texto": "uno"}, [pk]).json()["item"]["id"]
        self.post("item_editar", {"hecho": True}, [i])
        self.assertTrue(self.listar().json()["postits"][0]["items"][0]["hecho"])
        self.assertEqual(self.post("item_editar", {"hecho": True}, [i], self.otro()).status_code, 404)
        self.post("item_borrar", {}, [i])
        self.assertEqual(self.listar().json()["postits"][0]["items"], [])

    def test_login_requerido(self):
        self.client.logout()
        self.assertEqual(self.listar().status_code, 302)


class ProyectoTests(PostitsBase):
    tipo = "proyectos.proyecto"

    def crear(self, **extra):
        return self.post("crear", {"tipo": self.tipo, "id": self.proy.pk, "texto": "n", **extra})

    def test_tipo_fuera_de_whitelist(self):
        r = self.post("crear", {"tipo": "auth.user", "id": self.u.pk})
        self.assertEqual(r.status_code, 400)

    def test_privada_no_la_ve_otro_con_acceso(self):
        AccesoSitio.objects.create(user=self.o, empresa="AJ", sitio="S1")
        self.crear()
        r = self.listar(self.otro(), tipo=self.tipo, id=self.proy.pk)
        self.assertEqual(r.json()["postits"], [])

    def test_compartida_solo_lectura_para_otro(self):
        AccesoSitio.objects.create(user=self.o, empresa="AJ", sitio="S1")
        pk = self.crear(compartida=True).json()["postit"]["id"]
        c = self.otro()
        notas = self.listar(c, tipo=self.tipo, id=self.proy.pk).json()["postits"]
        self.assertEqual(len(notas), 1)
        self.assertFalse(notas[0]["es_mio"])
        self.assertEqual(self.post("editar", {"texto": "z"}, [pk], c).status_code, 404)

    def test_sin_acceso_al_sitio_403(self):
        c = self.otro()
        self.assertEqual(self.listar(c, tipo=self.tipo, id=self.proy.pk).status_code, 403)
        r = self.post("crear", {"tipo": self.tipo, "id": self.proy.pk}, client=c)
        self.assertEqual(r.status_code, 403)

    def test_general_no_aparece_en_proyecto(self):
        self.post("crear", {"texto": "g"})
        self.assertEqual(self.listar(tipo=self.tipo, id=self.proy.pk).json()["postits"], [])


@override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})
class WidgetTests(PostitsBase):
    def render(self, user):
        req = RequestFactory().get("/")
        req.user = user
        return Template("{% load postits %}{% postits_widget %}").render(Context({"request": req}))

    def test_anonimo_no_renderiza(self):
        from django.contrib.auth.models import AnonymousUser
        self.assertNotIn("postits-fab", self.render(AnonymousUser()))

    def test_autenticado_renderiza(self):
        self.assertIn("postits-fab", self.render(self.u))
