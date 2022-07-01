from rest_framework.permissions import IsAuthenticated
from user.models import is_shopper, is_wholesaler


class IsAuthenticatedShopper(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and is_shopper(request.user)


class IsAuthenticatedWholesaler(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and is_wholesaler(request.user)


class IsAdminUser(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_admin


class IsEasyAdminUser(IsAdminUser):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.username == 'easyadmin'