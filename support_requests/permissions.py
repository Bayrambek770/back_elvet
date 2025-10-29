"""Custom permissions for Request management."""

from rest_framework import permissions


def _is_moderator_or_admin(user) -> bool:
    return bool(user and user.is_authenticated and (getattr(user, "role", None) == "moderator" or user.is_staff))


class IsModeratorOrReadOnly(permissions.BasePermission):
    """Allow SAFE_METHODS for moderators/admins; POST is open (anonymous allowed); writes only for moderators/admins."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return _is_moderator_or_admin(request.user)
        if request.method == "POST":
            # Anonymous creation is allowed per requirements
            return True
        return _is_moderator_or_admin(request.user)
