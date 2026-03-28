from rest_framework.permissions import BasePermission

class IsAdminRole(BasePermission):
    """Allow access only to users with role='admin'"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_role_admin

class IsStaffOrAdmin(BasePermission):
    """Allow access only to users with role='staff' or role='admin'"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.is_role_admin or request.user.is_role_staff)