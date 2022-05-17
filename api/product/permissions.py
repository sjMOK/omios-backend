from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, SAFE_METHODS
from user.models import is_shopper, is_wholesaler


class ProductPermission(IsAuthenticated):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        elif super().has_permission(request, view) and is_wholesaler(request.user):
            return True

        return False

    def has_object_permission(self, request, view, obj):
        if is_wholesaler(request.user):
            return obj.wholesaler_id == request.user.id
        return True


class ProductQuestionAnswerPermission(IsAuthenticatedOrReadOnly):
    def has_object_permission(self, request, view, obj):
        if is_shopper(request.user):
            return obj.shopper_id == request.user.id
        return False
