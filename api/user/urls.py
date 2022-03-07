from django.urls import path

from .documentation import (
    decorated_issuing_token_view, decorated_refreshing_token_view, decorated_blacklisting_token_view,
    decorated_shopper_view, decorated_wholesaler_view, decorated_upload_business_registration_image_view,
    decorated_get_buildings_view, decorated_user_password_view, decorated_is_unique_view
)


app_name = 'user'

token_urlpatterns = [
    path('', decorated_issuing_token_view),
    path('refresh/', decorated_refreshing_token_view),
    path('blacklist/', decorated_blacklisting_token_view),
]

urlpatterns = [
    path('shopper/', decorated_shopper_view),
    path('wholesaler/', decorated_wholesaler_view),
    path('wholesaler/business_registration_image/', decorated_upload_business_registration_image_view),
    path('wholesaler/building/', decorated_get_buildings_view),
    path('password/', decorated_user_password_view),
    path('unique/', decorated_is_unique_view),
]
