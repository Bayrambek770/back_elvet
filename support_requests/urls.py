from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import RequestViewSet

app_name = "support_requests"

router = DefaultRouter()
router.register(r"requests", RequestViewSet, basename="request")

urlpatterns = [
    path("", include(router.urls)),
]
