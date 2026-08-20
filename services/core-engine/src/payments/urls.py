from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    EsewaCallbackAPIView, EscrowLedgerViewSet, KhaltiCallbackAPIView,
    PaymentTransactionViewSet,
)

router = DefaultRouter()
router.register(r'payments', PaymentTransactionViewSet, basename='payment')
router.register(r'escrow', EscrowLedgerViewSet, basename='escrow')

urlpatterns = [
    path('callbacks/khalti/', KhaltiCallbackAPIView.as_view(), name='khalti-callback'),
    path('callbacks/esewa/', EsewaCallbackAPIView.as_view(), name='esewa-callback'),
    path('', include(router.urls)),
]
