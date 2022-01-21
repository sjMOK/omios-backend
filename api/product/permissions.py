from rest_framework import permissions


class ProductPermission(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        elif super().has_permission(request, view) and hasattr(request.user, 'wholesaler'):
            return True
            
        return False

    def has_object_permission(self, request, view, obj):
        if hasattr(request.user, 'wholesaler'):
            return obj.wholesaler_id == request.user.id
        return True
