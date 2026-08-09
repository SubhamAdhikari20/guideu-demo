from django.urls import path

from .views import ArrivalsForecastView, GuideRecommendationsView, RouteRecommendationsView

urlpatterns = [
    path("routes/", RouteRecommendationsView.as_view(), name="recommend-routes"),
    path("guides/", GuideRecommendationsView.as_view(), name="recommend-guides"),
    path("forecast/", ArrivalsForecastView.as_view(), name="arrivals-forecast"),
]
