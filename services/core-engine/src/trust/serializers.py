from __future__ import annotations

from rest_framework import serializers

from src.catalog.models import Region

from .models import PriceCheck, ScamReport


class ScamReportSerializer(serializers.ModelSerializer):
    reporter = serializers.PrimaryKeyRelatedField(read_only=True)
    region = serializers.SlugRelatedField(slug_field="name", queryset=Region.objects.all())

    class Meta:
        model = ScamReport
        fields = (
            "id", "reporter", "service_type", "region", "season",
            "quoted_price_npr", "benchmark_price_npr", "overcharge_ratio",
            "scam_severity", "was_flagged_by_app", "ml_scam_probability",
            "status", "verified_by_moderator", "description", "created_at",
        )
        # Derived/trust fields are computed server-side, never client-supplied.
        read_only_fields = (
            "benchmark_price_npr", "overcharge_ratio", "scam_severity",
            "was_flagged_by_app", "ml_scam_probability", "status",
            "verified_by_moderator", "created_at",
        )


class PriceCheckRequestSerializer(serializers.Serializer):
    service_type = serializers.CharField()
    region = serializers.CharField(required=False, allow_blank=True)
    season = serializers.CharField(required=False, allow_blank=True)
    quoted_price_npr = serializers.IntegerField(min_value=1)


class PriceCheckResultSerializer(serializers.Serializer):
    service_type = serializers.CharField()
    region = serializers.CharField(allow_null=True)
    season = serializers.CharField(allow_null=True)
    quoted_price_npr = serializers.IntegerField()
    benchmark_price_npr = serializers.IntegerField(allow_null=True)
    overcharge_ratio = serializers.FloatField(allow_null=True)
    is_likely_scam = serializers.BooleanField()
    severity = serializers.CharField(allow_null=True)
    scam_probability = serializers.FloatField(allow_null=True)
    source = serializers.CharField()
    explanation = serializers.ListField(child=serializers.CharField())
    # Fair-wage protection for guides and porters (see services.check_price).
    below_fair_wage = serializers.BooleanField(default=False)
    below_fair_range = serializers.BooleanField(default=False)
    fair_wage_message = serializers.CharField(allow_null=True, required=False)


class PriceCheckLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceCheck
        fields = (
            "id", "service_type", "region", "season", "quoted_price_npr",
            "benchmark_price_npr", "overcharge_ratio", "is_likely_scam", "source", "created_at",
        )
        read_only_fields = fields
