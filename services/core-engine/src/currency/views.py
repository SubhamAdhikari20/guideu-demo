from __future__ import annotations

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services


class CurrencyRatesView(APIView):
    """``GET /api/v1/currency/rates/`` — current NPR-based exchange rates."""

    permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):
        return Response({"base": "NPR", "rates": services.get_rates()})


class CurrencyConvertView(APIView):
    """``GET /api/v1/currency/convert/?amount=5000&to=USD``."""

    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[
            OpenApiParameter("amount", float, required=True),
            OpenApiParameter("to", str, required=True),
        ]
    )
    def get(self, request, *args, **kwargs):
        try:
            amount = float(request.query_params.get("amount", ""))
        except (TypeError, ValueError):
            return Response({"detail": "amount must be a number."}, status=400)
        to = (request.query_params.get("to") or "NPR").upper()
        if to not in services.SUPPORTED_CURRENCIES:
            return Response({"detail": f"Unsupported currency: {to}."}, status=400)
        return Response(
            {
                "amount_npr": amount,
                "to": to,
                "converted": services.convert(amount, to),
                "rate": services.get_rates().get(to, 1.0),
            }
        )
