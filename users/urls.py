from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AdminViewSet, ModeratorViewSet, DoctorViewSet, NurseViewSet, ClientViewSet

app_name = "users"

router = DefaultRouter()
router.register(r"admins", AdminViewSet, basename="admin")
router.register(r"moderators", ModeratorViewSet, basename="moderator")
router.register(r"doctors", DoctorViewSet, basename="doctor")
router.register(r"nurses", NurseViewSet, basename="nurse")
router.register(r"clients", ClientViewSet, basename="client")

urlpatterns = [
    path("", include(router.urls)),
]
