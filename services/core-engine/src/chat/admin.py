from django.contrib import admin

from .models import ChatMessage, ChatThread


@admin.register(ChatThread)
class ChatThreadAdmin(admin.ModelAdmin):
    list_display = ("room", "updated_at")
    search_fields = ("room",)
    filter_horizontal = ("participants",)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("thread", "sender", "is_read", "created_at")
    list_filter = ("is_read",)
    search_fields = ("body",)
