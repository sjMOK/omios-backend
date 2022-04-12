from rest_framework.permissions import IsAuthenticated


class OrderPermission(IsAuthenticated):
    def has_permission(self, request, view):
        if not hasattr(request.user, 'shopper'):
            return False

        return super().has_permission(request, view)

    def _get_shopper(obj):
        return obj.shopper

    def has_object_permission(self, request, view, obj):
        if request.user.shopper == self._get_shopper(obj):
            return True

        return False


class OrderItemPermission(OrderPermission):
    def _get_shopper(obj):
        return obj.order.shopper
    