from rest_framework.permissions import IsAuthenticated
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
