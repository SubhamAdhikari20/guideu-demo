from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .models import PriceCheck, ScamReport, classify_severity
from .serializers import (
    PriceCheckRequestSerializer,
    PriceCheckResultSerializer,
    ScamReportSerializer,
)
from .services import SCAM_RATIO_THRESHOLD, check_price


class ScamReportViewSet(viewsets.ModelViewSet):
    """Tourists report overcharges. Trust fields are computed server-side."""

    serializer_class = ScamReportSerializer
    permission_classes = (IsAuthenticated,)
    filterset_fields = ("service_type", "scam_severity", "status", "was_flagged_by_app")
    search_fields = ("service_type", "description")
    ordering_fields = ("created_at", "overcharge_ratio")

    def get_queryset(self):
        user = self.request.user
        qs = ScamReport.objects.select_related("region", "reporter")
        if user.is_authenticated and user.is_staff:
            return qs
        return qs.filter(reporter=user)

    def perform_create(self, serializer):
        region = serializer.validated_data["region"]
        result = check_price(
            service_type=serializer.validated_data["service_type"],
            region=region.name,
            season=serializer.validated_data.get("season") or None,
            quoted_price_npr=serializer.validated_data["quoted_price_npr"],
        )
        benchmark = result.benchmark_price_npr or serializer.validated_data["quoted_price_npr"]
        ratio = result.overcharge_ratio or 1.0
        serializer.save(
            reporter=self.request.user,
            benchmark_price_npr=benchmark,
            overcharge_ratio=ratio,
            scam_severity=result.severity or classify_severity(ratio),
            was_flagged_by_app=ratio > SCAM_RATIO_THRESHOLD,
            ml_scam_probability=result.scam_probability,
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def verify(self, request, pk=None, *args, **kwargs):
        report = self.get_object()
        report.status = ScamReport.Status.VERIFIED
        report.verified_by_moderator = True
        report.save(update_fields=["status", "verified_by_moderator", "updated_at"])
        return Response(ScamReportSerializer(report).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def dismiss(self, request, pk=None, *args, **kwargs):
        report = self.get_object()
        report.status = ScamReport.Status.DISMISSED
        report.save(update_fields=["status", "updated_at"])
        return Response(ScamReportSerializer(report).data)


class PriceCheckView(APIView):
    """The headline anti-scam tool: 'is this price fair?'.

    Resolves the fair benchmark, computes the overcharge ratio, and returns an
    explainable verdict (ML-scored when the analytics-engine is reachable, else
    a deterministic benchmark rule). Rate-limited per the ``scam_check`` scope.
    """

    permission_classes = (IsAuthenticated,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "scam_check"

    @extend_schema(request=PriceCheckRequestSerializer, responses=PriceCheckResultSerializer)
    def post(self, request, *args, **kwargs):
        # *args/**kwargs matter: URLPathVersioning passes `version="v1"` into the
        # handler, so a bare `post(self, request)` raises TypeError on every call.
        payload = PriceCheckRequestSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data

        result = check_price(
            service_type=data["service_type"],
            region=data.get("region") or None,
            season=data.get("season") or None,
            quoted_price_npr=data["quoted_price_npr"],
        )

        PriceCheck.objects.create(
            actor=request.user,
            service_type=result.service_type,
            region=result.region or "",
            season=result.season or "",
            quoted_price_npr=result.quoted_price_npr,
            benchmark_price_npr=result.benchmark_price_npr,
            overcharge_ratio=result.overcharge_ratio,
            is_likely_scam=result.is_likely_scam,
            source=result.source,
        )
        return Response(PriceCheckResultSerializer(result.as_dict()).data, status=status.HTTP_200_OK)
