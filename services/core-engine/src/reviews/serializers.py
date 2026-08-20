from __future__ import annotations

from typing import Any

from rest_framework import serializers

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(read_only=True)
    author_username = serializers.CharField(source="author.username", read_only=True)
    target_kind = serializers.ReadOnlyField()

    class Meta:
        model = Review
        fields = (
            "id", "author", "author_username", "guide", "guide_account", "route", "booking",
            "rating", "title", "comment", "status", "is_flagged", "helpful_count",
            "target_kind", "created_at",
        )
        read_only_fields = ("status", "is_flagged", "helpful_count", "created_at")

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        guide = data.get("guide", getattr(self.instance, "guide", None))
        guide_account = data.get("guide_account", getattr(self.instance, "guide_account", None))
        route = data.get("route", getattr(self.instance, "route", None))
        if sum(bool(target) for target in (guide, guide_account, route)) != 1:
            raise serializers.ValidationError("Provide exactly one guide account, catalog guide, or route.")
        if guide_account:
            from src.authentication.models import User
            from src.bookings.models import GuideRequest
            request = self.context.get('request')
            if guide_account.role != User.Roles.GUIDE:
                raise serializers.ValidationError({'guide_account': 'The selected account is not a guide.'})
            if request and not request.user.is_staff and not GuideRequest.objects.filter(
                tourist=request.user, accepted_guide=guide_account,
                status=GuideRequest.Status.COMPLETED,
            ).exists():
                raise serializers.ValidationError({'guide_account': 'Complete a trip with this guide before reviewing them.'})
        comment = data.get("comment", "")
        if comment and len(comment.strip()) < 3:
            raise serializers.ValidationError({"comment": "Comment is too short."})
        return data


class ReviewSummarySerializer(serializers.Serializer):
    average_rating = serializers.FloatField()
    review_count = serializers.IntegerField()


class ModerateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Review.Status.choices)
