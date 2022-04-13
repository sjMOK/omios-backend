from django.urls import path, include

from .documentation import (
    decorated_issuing_token_view, decorated_refreshing_token_view, decorated_blacklisting_token_view,
    decorated_upload_business_registration_image_view, decorated_get_buildings_view, decorated_user_password_view,
    decorated_is_unique_view, decorated_product_like_view,
)

app_name = 'user'

token_urlpatterns = [
    path('', decorated_issuing_token_view),
    path('/refresh', decorated_refreshing_token_view),
    path('/blacklist', decorated_blacklisting_token_view),
]

wholesaler_url_patterns = [
    path('/business_registration_images', decorated_upload_business_registration_image_view),
    path('/buildings', decorated_get_buildings_view),
]

urlpatterns = [
    path('/tokens', include(token_urlpatterns)),
    path('/wholesalers', include(wholesaler_url_patterns)),
    path('/passwords', decorated_user_password_view),
    path('/unique', decorated_is_unique_view),
    path('/shoppers/<int:user_id>/like/<int:product_id>', decorated_product_like_view),
]
