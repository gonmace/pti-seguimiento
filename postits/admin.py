from django.contrib import admin

from .models import Postit, PostitItem


class PostitItemInline(admin.TabularInline):
    model = PostitItem
    extra = 0


@admin.register(Postit)
class PostitAdmin(admin.ModelAdmin):
    list_display = ("__str__", "autor", "color", "compartida", "archivada", "recordatorio",
                    "content_type", "object_id")
    list_filter = ("color", "compartida", "archivada")
    inlines = [PostitItemInline]
