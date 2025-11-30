"""URL-маршруты для приложения Users."""

from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .views import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    CustomTokenVerifyView,
    LogoutView,
    SessionTokenView,
    UserViewSet,
)

app_name = "users"

router = DefaultRouter()
router.register(r"", UserViewSet, basename="users")

urlpatterns = [
    path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", CustomTokenVerifyView.as_view(), name="token_verify"),
    path("token/session/", SessionTokenView.as_view(), name="token_session"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("", include(router.urls)),
]
