from common.permissions import IsAuthenticatedShopper

class OrderPermission(IsAuthenticatedShopper):
    def _get_shopper_id(self, obj):
        return obj.shopper_id

    def has_object_permission(self, request, view, obj):
        if request.user.id == self._get_shopper_id(obj):
            return True

        return False


class OrderItemPermission(OrderPermission):
    def _get_shopper_id(self, obj):
        return obj.order.shopper_id
    