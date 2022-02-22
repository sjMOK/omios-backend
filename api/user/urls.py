from django.urls import path

from . import documentation


app_name = 'user'

token_urlpatterns = [
    path('', documentation.decorated_issuing_token_view),
    path('refresh/', documentation.decorated_refreshing_token_view),
    path('blacklist/', documentation.decorated_blacklisting_token_view),
]

urlpatterns = [
    path('shopper/', documentation.decorated_shopper_view),
    path('wholesaler/', documentation.decorated_wholesaler_view),
    path('password/', documentation.decorated_user_password_view),
    path('unique/', documentation.decorated_is_unique_view),
]
