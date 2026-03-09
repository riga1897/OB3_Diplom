"""URL configuration for OB3 Document Processing Service."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.views import serve as staticfiles_serve
from django.urls import include, path
from django.views.decorators.cache import cache_control
from django.views.generic.base import RedirectView

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from apps.core.views import api_root, health_check
from apps.users.views import RegisterView


@cache_control(max_age=86400, public=True)
def favicon_view(request):  # type: ignore[no-untyped-def]
    """Отдаём favicon.ico из static/."""
    return staticfiles_serve(request, "favicon.ico")


urlpatterns = [
    # Favicon — браузеры запрашивают /favicon.ico напрямую
    path("favicon.ico", favicon_view, name="favicon"),
    # Root redirect to API root
    path("", RedirectView.as_view(url="/api/", permanent=False), name="root-redirect"),
    path("admin/", admin.site.urls),
    # DRF browsable API authentication (login/logout для веб-интерфейса)
    path("api/auth/", include("rest_framework.urls", namespace="rest_framework")),
    # API Root - список всех доступных endpoints
    path("api/", api_root, name="api-root"),
    # User registration
    path("api/register/", RegisterView.as_view(), name="register"),
    # Health check
    path("health/", health_check, name="health_check"),
    # API documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    # API endpoints
    path("api/users/", include("apps.users.urls")),
    path("api/documents/", include("apps.documents.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
