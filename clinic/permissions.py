"""Permissions for Nurse Management System (schedules, tasks)."""

from rest_framework import permissions


def _is_doctor(user) -> bool:
    return bool(user and user.is_authenticated and getattr(user, "role", None) == "doctor")


def _is_nurse(user) -> bool:
    return bool(user and user.is_authenticated and getattr(user, "role", None) == "nurse")


def _is_admin_or_moderator(user) -> bool:
    role = getattr(user, "role", None)
    return bool(user and user.is_authenticated and (getattr(user, "is_staff", False) or role in {"admin", "moderator"}))


class IsDoctorForScheduleWrite(permissions.BasePermission):
    """Only doctors can create/update/delete schedules; others read-only."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return _is_doctor(request.user)


class IsDoctorOrAssignedNurseForTask(permissions.BasePermission):
    """Allow doctors or the assigned nurse to access/modify tasks.

    - Doctors: full access
    - Nurses: only if they are assigned to the task
    """

    def has_object_permission(self, request, view, obj):
        if _is_doctor(request.user):
            return True
        if _is_nurse(request.user):
            return getattr(obj, "nurse", None) and getattr(obj.nurse, "user_id", None) == request.user.id
        return False

    def has_permission(self, request, view):
        # Allow reads to authenticated users
        if request.method in permissions.SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        # Creation allowed only for doctors or admins/moderators
        if request.method == "POST":
            return bool(_is_doctor(request.user) or _is_admin_or_moderator(request.user))
        # Updates/deletes require authentication; object-level will verify ownership/role
        return bool(request.user and request.user.is_authenticated)


class IsDoctorOwnerOrAdmin(permissions.BasePermission):
    """Doctors can access their own objects; admins/moderators can access all.

    For creation/update, only doctors can perform writes on their own objects.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        # Only doctors can write
        return _is_doctor(request.user)

    def has_object_permission(self, request, view, obj):
        if _is_admin_or_moderator(request.user):
            return True
        if _is_doctor(request.user):
            owner = getattr(obj, "doctor", None)
            return owner and getattr(owner, "user_id", None) == request.user.id
        return False


class IsNurseOwnerOrAdmin(permissions.BasePermission):
    """Nurses can access their own objects; admins/moderators can access all."""

    def has_permission(self, request, view):
        # Read-only viewsets typically; ensure user is authenticated for any access
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if _is_admin_or_moderator(request.user):
            return True
        if _is_nurse(request.user):
            owner = getattr(obj, "nurse", None)
            return owner and getattr(owner, "user_id", None) == request.user.id
        return False


class IsModeratorWriteVisits(permissions.BasePermission):
    """Only moderators can create/update/delete Visit records.

    Read access allowed to authenticated users; filtering will be applied in the view.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        # Only moderators can write
        return bool(request.user and request.user.is_authenticated and getattr(request.user, "role", None) == "moderator")
