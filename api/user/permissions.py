from rest_framework.permissions import IsAuthenticated, AllowAny


class IsAuthenticatedExceptCreate(IsAuthenticated):
    __detail_view_method = ('GET', 'PATCH', 'DELETE')
    
    def has_permission(self, request, view):
        if request.method in self.__detail_view_method:
            return super().has_permission(request, view)
        else:
            return True
