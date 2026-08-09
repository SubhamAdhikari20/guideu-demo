from __future__ import annotations

from rest_framework import serializers

from src.common.sanitize import clean_text

from .models import TravelWorkspace, WorkspaceItem


class WorkspaceItemSerializer(serializers.ModelSerializer):
    title = serializers.ReadOnlyField()

    class Meta:
        model = WorkspaceItem
        fields = (
            "id", "workspace", "item_type", "title", "route", "guide", "package",
            "custom_title", "custom_description", "day_number", "display_order",
            "start_time", "duration_minutes", "estimated_cost_npr", "is_booked",
        )

    def validate_workspace(self, workspace):
        """A user may only add items to their own workspace."""
        request = self.context.get("request")
        if request and workspace.tourist_id != request.user.id:
            raise serializers.ValidationError("Not your workspace.")
        return workspace

    def validate_custom_title(self, value: str) -> str:
        return clean_text(value)

    def validate_custom_description(self, value: str) -> str:
        return clean_text(value)


class TravelWorkspaceSerializer(serializers.ModelSerializer):
    item_count = serializers.IntegerField(source="items.count", read_only=True)
    total_planned_cost_npr = serializers.ReadOnlyField()
    trip_days = serializers.ReadOnlyField()

    class Meta:
        model = TravelWorkspace
        fields = (
            "id", "title", "start_date", "end_date", "total_budget_npr",
            "currency_preference", "notes", "item_count", "total_planned_cost_npr",
            "trip_days", "created_at",
        )
        read_only_fields = ("created_at",)

    def validate(self, attrs):
        start = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if start and end and end < start:
            raise serializers.ValidationError({"end_date": "End date must be on or after the start date."})
        return attrs


class TravelWorkspaceDetailSerializer(TravelWorkspaceSerializer):
    items = WorkspaceItemSerializer(many=True, read_only=True)

    class Meta(TravelWorkspaceSerializer.Meta):
        fields = TravelWorkspaceSerializer.Meta.fields + ("items",)


class ReorderItemSerializer(serializers.Serializer):
    item_id = serializers.IntegerField()
    day_number = serializers.IntegerField(min_value=1)
    display_order = serializers.IntegerField(min_value=0)
