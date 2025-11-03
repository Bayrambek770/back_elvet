"""ViewSets for user roles (Admin, Moderator, Doctor, Nurse, Client) and user creation API."""

from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Admin, Moderator, Doctor, Nurse, Client, RoleChoices
from .serializers import (
    AdminSerializer,
    ModeratorSerializer,
    DoctorSerializer,
    NurseSerializer,
    ClientSerializer,
    CreateUserSerializer,
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

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        role = getattr(user, "role", None)
        if role == RoleChoices.CLIENT:
            client = getattr(user, "client_profile", None)
            return qs.filter(pk=getattr(client, "pk", None)) if client else qs.none()
        if role in {RoleChoices.ADMIN, RoleChoices.MODERATOR} or getattr(user, "is_staff", False):
            return qs
        return qs

    def update(self, request, *args, **kwargs):
        # Allow clients to update only their own record; admins/moderators can update any
        instance = self.get_object()
        user = request.user
        role = getattr(user, "role", None)
        if role == RoleChoices.CLIENT and getattr(instance, "user_id", None) != user.id:
            return Response({"detail": "You can only update your own profile."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        role = getattr(user, "role", None)
        if role == RoleChoices.CLIENT and getattr(instance, "user_id", None) != user.id:
            return Response({"detail": "You can only update your own profile."}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)


class CreateUserView(APIView):
    """Create a new user and trigger role-profile auto-creation via signals.

    Access control:
    - Admins (role="admin" or is_superuser): can create any role (admin/moderator/doctor/nurse/client).
    - Moderators: can create clients only.
    - Anonymous users: can create clients only (self-registration).
    - Authenticated non-admin/non-moderator users (e.g., client/doctor/nurse): not allowed to create any user.
    """

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=["users"],
        summary="Create new user",
        request=CreateUserSerializer,
        responses={201: CreateUserSerializer},
        description=(
            "Create a new user by providing first_name, last_name, phone_number, password, and role.\n"
            "If caller is not staff, only role=client is allowed. Role-specific profiles are auto-created via signals."
        ),
    )
    def post(self, request, *args, **kwargs):
        serializer = CreateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        requested_role = serializer.validated_data.get("role")

        req_user = getattr(request, "user", None)
        is_auth = bool(getattr(req_user, "is_authenticated", False))
        is_super = bool(getattr(req_user, "is_superuser", False))
        user_role = getattr(req_user, "role", None) if is_auth else None

        # Determine allowed roles based on requester
        if is_super or user_role == RoleChoices.ADMIN:
            allowed_roles = {
                RoleChoices.ADMIN,
                RoleChoices.MODERATOR,
                RoleChoices.DOCTOR,
                RoleChoices.NURSE,
                RoleChoices.CLIENT,
            }
        elif user_role == RoleChoices.MODERATOR:
            allowed_roles = {RoleChoices.CLIENT}
        elif not is_auth:
            # Anonymous self-registration
            allowed_roles = {RoleChoices.CLIENT}
        else:
            # Authenticated but not admin/moderator (client/doctor/nurse) -> none
            allowed_roles = set()

        if requested_role not in allowed_roles:
            return Response(
                {"detail": "You are not allowed to create the requested role."},
                status=status.HTTP_403_FORBIDDEN,
            )

        instance = serializer.save()
        out = CreateUserSerializer(instance)
        return Response(out.data, status=status.HTTP_201_CREATED)
