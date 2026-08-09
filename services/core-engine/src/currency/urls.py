from django.urls import path

from .views import CurrencyConvertView, CurrencyRatesView

urlpatterns = [
    path("rates/", CurrencyRatesView.as_view(), name="currency-rates"),
    path("convert/", CurrencyConvertView.as_view(), name="currency-convert"),
]
