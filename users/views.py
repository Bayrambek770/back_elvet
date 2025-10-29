"""ViewSets for user roles (Admin, Moderator, Doctor, Nurse, Client)."""

from rest_framework import permissions, viewsets
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Admin, Moderator, Doctor, Nurse, Client
from .serializers import (
    AdminSerializer,
    ModeratorSerializer,
    DoctorSerializer,
    NurseSerializer,
    ClientSerializer,
)


@extend_schema_view(
    list=extend_schema(tags=["users:admins"], summary="List admins"),
    retrieve=extend_schema(tags=["users:admins"], summary="Retrieve admin"),
    create=extend_schema(tags=["users:admins"], summary="Create admin"),
    update=extend_schema(tags=["users:admins"], summary="Update admin"),
    partial_update=extend_schema(tags=["users:admins"], summary="Partially update admin"),
    destroy=extend_schema(tags=["users:admins"], summary="Delete admin"),
)
class AdminViewSet(viewsets.ModelViewSet):
    queryset = Admin.objects.select_related("user").all()
    serializer_class = AdminSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema_view(
    list=extend_schema(tags=["users:moderators"], summary="List moderators"),
    retrieve=extend_schema(tags=["users:moderators"], summary="Retrieve moderator"),
    create=extend_schema(tags=["users:moderators"], summary="Create moderator"),
    update=extend_schema(tags=["users:moderators"], summary="Update moderator"),
    partial_update=extend_schema(tags=["users:moderators"], summary="Partially update moderator"),
    destroy=extend_schema(tags=["users:moderators"], summary="Delete moderator"),
)
class ModeratorViewSet(viewsets.ModelViewSet):
    queryset = Moderator.objects.select_related("user", "created_by__user").all()
    serializer_class = ModeratorSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema_view(
    list=extend_schema(tags=["users:doctors"], summary="List doctors"),
    retrieve=extend_schema(tags=["users:doctors"], summary="Retrieve doctor"),
    create=extend_schema(tags=["users:doctors"], summary="Create doctor"),
    update=extend_schema(tags=["users:doctors"], summary="Update doctor"),
    partial_update=extend_schema(tags=["users:doctors"], summary="Partially update doctor"),
    destroy=extend_schema(tags=["users:doctors"], summary="Delete doctor"),
)
class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.select_related("user", "created_by__user").all()
    serializer_class = DoctorSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema_view(
    list=extend_schema(tags=["users:nurses"], summary="List nurses"),
    retrieve=extend_schema(tags=["users:nurses"], summary="Retrieve nurse"),
    create=extend_schema(tags=["users:nurses"], summary="Create nurse"),
    update=extend_schema(tags=["users:nurses"], summary="Update nurse"),
    partial_update=extend_schema(tags=["users:nurses"], summary="Partially update nurse"),
    destroy=extend_schema(tags=["users:nurses"], summary="Delete nurse"),
)
class NurseViewSet(viewsets.ModelViewSet):
    queryset = Nurse.objects.select_related("user", "created_by__user").all()
    serializer_class = NurseSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema_view(
    list=extend_schema(tags=["users:clients"], summary="List clients"),
    retrieve=extend_schema(tags=["users:clients"], summary="Retrieve client"),
    create=extend_schema(tags=["users:clients"], summary="Create client"),
    update=extend_schema(tags=["users:clients"], summary="Update client"),
    partial_update=extend_schema(tags=["users:clients"], summary="Partially update client"),
    destroy=extend_schema(tags=["users:clients"], summary="Delete client"),
)
class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.select_related("user", "created_by__user").all()
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]
