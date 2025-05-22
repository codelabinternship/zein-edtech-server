from rest_framework import permissions
from rest_framework.permissions import BasePermission


class IsAdminOrReadOnly(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user and request.user.is_staff


class IsSuperAdminOrDev(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ["super_admin", "dev"]