from django.urls import path

from .views import GuideRecommendationsView, RouteRecommendationsView

urlpatterns = [
    path("routes/", RouteRecommendationsView.as_view(), name="recommend-routes"),
    path("guides/", GuideRecommendationsView.as_view(), name="recommend-guides"),
]
