from rest_framework.permissions import IsAuthenticated, BasePermission
from user.models import is_shopper, is_wholesaler


class IsAuthenticatedShopper(IsAuthenticated):
    def has_permission(self, request, view):
        if super().has_permission(request, view) and is_shopper(request.user):
            return True
        return False


class IsAuthenticatedWholesaler(IsAuthenticated):
    def has_permission(self, request, view):
        if super().has_permission(request, view) and is_wholesaler(request.user):
            return True
        return False


class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.is_admin)
