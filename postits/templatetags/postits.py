from django import template
from django.middleware.csrf import get_token
from django.urls import reverse

register = template.Library()


@register.inclusion_tag("postits/widget.html", takes_context=True)
def postits_widget(context):
    request = context.get("request")
    user = getattr(request, "user", None)
    if not (user and user.is_authenticated):
        return {"activo": False}
    return {
        "activo": True,
        "csrf": get_token(request),
        "urls": {
            "listar": reverse("postits:listar"),
            "resumen": reverse("postits:resumen"),
            "crear": reverse("postits:crear"),
            "base": reverse("postits:listar"),
        },
    }
