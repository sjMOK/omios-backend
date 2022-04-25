from rest_framework.permissions import IsAuthenticated


class OrderPermission(IsAuthenticated):
    def _get_shopper_id(self, obj):
        return obj.shopper_id
    
    def has_permission(self, request, view):
        if not request.user.is_shopper:
            return False

        return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        if request.user.id == self._get_shopper_id(obj):
            return True

        return False


class OrderItemPermission(OrderPermission):
    def _get_shopper_id(self, obj):
        return obj.order.shopper_id
    