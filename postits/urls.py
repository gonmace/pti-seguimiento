from django.urls import path

from . import views

app_name = "postits"

urlpatterns = [
    path("api/", views.api_listar, name="listar"),
    path("api/resumen/", views.api_resumen, name="resumen"),
    path("api/crear/", views.api_crear, name="crear"),
    path("api/reordenar/", views.api_reordenar, name="reordenar"),
    path("api/<int:pk>/editar/", views.api_editar, name="editar"),
    path("api/<int:pk>/borrar/", views.api_borrar, name="borrar"),
    path("api/<int:pk>/item/crear/", views.api_item_crear, name="item_crear"),
    path("api/item/<int:pk>/editar/", views.api_item_editar, name="item_editar"),
    path("api/item/<int:pk>/borrar/", views.api_item_borrar, name="item_borrar"),
]
