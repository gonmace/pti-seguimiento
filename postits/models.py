from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

COLORES = [
    ("amarillo", "Amarillo"),
    ("rosa", "Rosa"),
    ("verde", "Verde"),
    ("azul", "Azul"),
    ("naranja", "Naranja"),
]


class Postit(models.Model):
    """Nota adhesiva. Sin ``content_type`` es una nota general del usuario; con él, queda
    ligada a cualquier objeto (p. ej. un proyecto)."""

    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name="postits")
    texto = models.TextField(blank=True)
    color = models.CharField(max_length=10, choices=COLORES, default="amarillo")
    compartida = models.BooleanField(
        default=False, help_text="Visible (solo lectura) para quienes acceden al objeto.")
    fijada = models.BooleanField(default=False)
    archivada = models.BooleanField(default=False)
    recordatorio = models.DateField(null=True, blank=True)
    orden = models.IntegerField(default=0)

    content_type = models.ForeignKey(ContentType, null=True, blank=True,
                                     on_delete=models.CASCADE)
    object_id = models.CharField(max_length=64, null=True, blank=True)
    objeto = GenericForeignKey("content_type", "object_id")

    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fijada", "orden", "-actualizado"]
        indexes = [models.Index(fields=["content_type", "object_id"])]

    def __str__(self):
        return (self.texto[:40] or "(vacía)")

    @property
    def vencida(self):
        return bool(self.recordatorio and not self.archivada
                    and self.recordatorio < timezone.localdate())


class PostitItem(models.Model):
    """Ítem de checklist dentro de una nota."""

    postit = models.ForeignKey(Postit, on_delete=models.CASCADE, related_name="items")
    texto = models.CharField(max_length=255)
    hecho = models.BooleanField(default=False)
    orden = models.IntegerField(default=0)

    class Meta:
        ordering = ["orden", "pk"]

    def __str__(self):
        return self.texto
