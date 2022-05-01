from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, SAFE_METHODS


class ProductPermission(IsAuthenticated):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        elif super().has_permission(request, view) and hasattr(request.user, 'wholesaler'):
            return True
            
        return False

    def has_object_permission(self, request, view, obj):
        if hasattr(request.user, 'wholesaler'):
            return obj.wholesaler_id == request.user.id
        return True


class ProductQuestionAnswerPermission(IsAuthenticatedOrReadOnly):
    def has_object_permission(self, request, view, obj):
        if hasattr(request.user, 'shopper'):
            return obj.shopper_id == request.user.id
        return False
