from __future__ import annotations

from rest_framework import serializers


class RouteRecommendationQuerySerializer(serializers.Serializer):
    """Query params for the personalised route feed.

    The tourist profile is taken from the request (with sensible defaults) so the
    feed works even for a brand-new user who hasn't set any preferences yet.
    """

    adventure = serializers.FloatField(min_value=0, max_value=1, default=0.5)
    culture = serializers.FloatField(min_value=0, max_value=1, default=0.5)
    nature = serializers.FloatField(min_value=0, max_value=1, default=0.5)
    # The ranker was trained on all five survey scores, so all five are accepted.
    risk_tolerance = serializers.FloatField(min_value=0, max_value=1, default=0.5)
    price_sensitivity = serializers.FloatField(min_value=0, max_value=1, default=0.5)
    budget_band = serializers.CharField(required=False, allow_blank=True)
    season = serializers.CharField(required=False, allow_blank=True)
    top_k = serializers.IntegerField(min_value=1, max_value=50, default=5)

    def to_tourist(self) -> dict:
        d = self.validated_data
        return {
            "pref_adventure_score": d["adventure"],
            "pref_culture_score": d["culture"],
            "pref_nature_score": d["nature"],
            "risk_tolerance": d["risk_tolerance"],
            "price_sensitivity": d["price_sensitivity"],
            "budget_band": d.get("budget_band") or None,
        }


class GuideRecommendationQuerySerializer(serializers.Serializer):
    region = serializers.CharField(required=False, allow_blank=True)
    language = serializers.CharField(required=False, allow_blank=True)
    adventure = serializers.FloatField(min_value=0, max_value=1, default=0.5)
    culture = serializers.FloatField(min_value=0, max_value=1, default=0.5)
    nature = serializers.FloatField(min_value=0, max_value=1, default=0.5)
    risk_tolerance = serializers.FloatField(min_value=0, max_value=1, default=0.5)
    price_sensitivity = serializers.FloatField(min_value=0, max_value=1, default=0.5)
    experience_level = serializers.CharField(required=False, allow_blank=True)
    travel_style = serializers.CharField(required=False, allow_blank=True)
    top_k = serializers.IntegerField(min_value=1, max_value=50, default=10)

    def to_tourist(self) -> dict:
        d = self.validated_data
        return {
            "pref_adventure_score": d["adventure"],
            "pref_culture_score": d["culture"],
            "pref_nature_score": d["nature"],
            "risk_tolerance": d["risk_tolerance"],
            "price_sensitivity": d["price_sensitivity"],
            "experience_level": d.get("experience_level") or None,
            "travel_style": d.get("travel_style") or None,
            "region": d.get("region") or None,
            "language": d.get("language") or None,
        }


class ArrivalsForecastQuerySerializer(serializers.Serializer):
    """Query params for the demand-forecast endpoint (admin planning + busy-month hints)."""

    year = serializers.IntegerField(min_value=2020, max_value=2100, required=False)
    region = serializers.CharField(required=False, allow_blank=True)
