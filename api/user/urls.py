from django.urls import path
from . import documentation


app_name = 'user'

token_urlpatterns = [
    path('', documentation.decorated_access_token_view),
    path('refresh/', documentation.decorated_refresh_token_view),
    path('blacklist/', documentation.decorated_blacklist_token_view),
]

urlpatterns = [
    path('shopper/', documentation.decorated_shopper_view),
    path('wholesaler/', documentation.decorated_wholesaler_view),
    path('password/', documentation.decorated_user_password_view),
    path('unique/', documentation.decorated_is_unique_view),
]
