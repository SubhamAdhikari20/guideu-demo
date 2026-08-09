from django.contrib import admin

from .models import SosAlert


@admin.register(SosAlert)
class SosAlertAdmin(admin.ModelAdmin):
    list_display = ("user", "status", "source", "latitude", "longitude", "created_at")
    list_filter = ("status", "source")
    search_fields = ("user__email", "message")
