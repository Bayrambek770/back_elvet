"""ViewSet for Request management with role-based access control."""

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Request
from .permissions import IsModeratorOrReadOnly
from .serializers import RequestSerializer


@extend_schema_view(
    list=extend_schema(tags=["support:requests"], summary="List requests"),
    retrieve=extend_schema(tags=["support:requests"], summary="Retrieve request"),
    create=extend_schema(tags=["support:requests"], summary="Create request (public)"),
    update=extend_schema(tags=["support:requests"], summary="Update request (staff)"),
    partial_update=extend_schema(tags=["support:requests"], summary="Partially update request (staff)"),
    destroy=extend_schema(tags=["support:requests"], summary="Delete request (staff)"),
)
class RequestViewSet(viewsets.ModelViewSet):
    """CRUD API for Requests with custom answer action."""

    queryset = Request.objects.all()
    serializer_class = RequestSerializer

    def get_permissions(self):
        if self.action == "create":
            # Anonymous users can create requests
            return [permissions.AllowAny()]
        if self.action in {"list", "retrieve", "update", "partial_update", "destroy"}:
            # Moderators/admins only
            return [IsModeratorOrReadOnly()]
        if self.action == "answer_request":
            return [IsModeratorOrReadOnly()]
        return [permissions.IsAuthenticated()]

    @extend_schema(tags=["support:requests"], summary="Answer request (staff)")
    @action(detail=True, methods=["patch"], url_path="answer")
    def answer_request(self, request, pk=None):
        obj = self.get_object()
        if obj.is_answered:
            return Response({"detail": "Request already answered."}, status=status.HTTP_400_BAD_REQUEST)
        obj.is_answered = True
        obj.answered_by = request.user
        obj.save(update_fields=["is_answered", "answered_by"])
        serializer = self.get_serializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)
