"""Root URL configuration.

All REST endpoints are versioned under ``/api/<version>/`` (URLPathVersioning,
``v1`` only for now). OpenAPI schema + Swagger UI are served via drf-spectacular.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from . import views

# Versioned API surface. The leading ``api/<version>/`` prefix supplies the
# ``version`` kwarg that DRF's URLPathVersioning reads.
api_patterns = [
    path("auth/", include("src.authentication.urls")),
    path("catalog/", include("src.catalog.urls")),
    path("bookings/", include("src.bookings.urls")),
    path("permits/", include("src.permits.urls")),
    path("payments/", include("src.payments.urls")),
    path("reviews/", include("src.reviews.urls")),
    path("favorites/", include("src.favorites.urls")),
    path("notifications/", include("src.notifications.urls")),
    path("analytics/", include("src.analytics.urls")),
    path("recommendations/", include("src.recommendations.urls")),
    path("chat/", include("src.chat.urls")),
    path("workspace/", include("src.workspace.urls")),
    path("currency/", include("src.currency.urls")),
    path("safety/", include("src.safety.urls")),
    path("trust/", include("src.trust.urls")),
    path("gamification/", include("src.gamification.urls")),
]

urlpatterns = [
    path("", views.service_index, name="service-index"),
    path("healthz/", views.healthz, name="healthz"),
    path("admin/", admin.site.urls),
    # OpenAPI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    # Versioned REST API
    path("api/<version>/", include(api_patterns)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
