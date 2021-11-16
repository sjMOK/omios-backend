from rest_framework.permissions import IsAuthenticated, SAFE_METHODS


def is_owner(request_user_id, obj_user_id):
    if request_user_id == obj_user_id:
        return True
    else:
        return False

class IsOwnerOnly(IsAuthenticated):

    def has_object_permission(self, request, view, obj):
        return is_owner(request.user.id, obj.user_id)
    
class IsOwnerOrReadOnly(IsAuthenticated):

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        else:
            return is_owner(request.user.id, obj.user_id)