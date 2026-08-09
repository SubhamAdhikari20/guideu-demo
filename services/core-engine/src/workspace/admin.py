from django.contrib import admin

from .models import TravelWorkspace, WorkspaceItem


class WorkspaceItemInline(admin.TabularInline):
    model = WorkspaceItem
    extra = 0


@admin.register(TravelWorkspace)
class TravelWorkspaceAdmin(admin.ModelAdmin):
    list_display = ("title", "tourist", "start_date", "end_date", "total_budget_npr")
    search_fields = ("title", "tourist__email")
    inlines = [WorkspaceItemInline]


@admin.register(WorkspaceItem)
class WorkspaceItemAdmin(admin.ModelAdmin):
    list_display = ("workspace", "item_type", "day_number", "display_order", "estimated_cost_npr")
    list_filter = ("item_type",)
