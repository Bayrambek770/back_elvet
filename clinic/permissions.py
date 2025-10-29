"""Permissions for Nurse Management System (schedules, tasks)."""

from rest_framework import permissions


def _is_doctor(user) -> bool:
    return bool(user and user.is_authenticated and getattr(user, "role", None) == "doctor")


def _is_nurse(user) -> bool:
    return bool(user and user.is_authenticated and getattr(user, "role", None) == "nurse")


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
        # Allow list/create to authenticated users; object-level will restrict
        return bool(request.user and request.user.is_authenticated)
