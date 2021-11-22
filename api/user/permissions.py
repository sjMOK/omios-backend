from rest_framework.permissions import IsAuthenticated, AllowAny


class IsOwnerInDetailView(IsAuthenticated):
    __detail_view_method = ('GET', 'PATCH', 'DELETE')

    def has_permission(self, request, view):
        if request.method in self.__detail_view_method:
            return super().has_permission(request, view)
        else:
            return True

    def has_object_permission(self, request, view, obj):
        if request.method in self.__detail_view_method:
            if request.user.id == obj.user_id:
                return True
            else:
                return False
        else:
            return True