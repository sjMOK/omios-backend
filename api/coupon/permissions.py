from rest_framework.permissions import SAFE_METHODS, BasePermission, IsAuthenticatedOrReadOnly


class CouponPermission(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return False
