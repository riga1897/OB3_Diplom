"""URL-маршруты для приложения Documents."""

from rest_framework.routers import SimpleRouter

from .views import DocumentViewSet

app_name = "documents"

router = SimpleRouter()
router.register(r"", DocumentViewSet, basename="documents")

urlpatterns = router.urls
