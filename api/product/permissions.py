from django.contrib.auth.models import AnonymousUser
from rest_framework import permissions
from rest_framework.decorators import permission_classes

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
