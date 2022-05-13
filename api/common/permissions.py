from rest_framework.permissions import IsAuthenticated


class IsAuthenticatedShopper(IsAuthenticated):
    def has_permission(self, request, view):
        if super().has_permission(request, view) and hasattr(request.user, 'shopper'):
            return True
        return False
