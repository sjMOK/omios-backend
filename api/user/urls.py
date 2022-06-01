from django.urls import path, include

from rest_framework.routers import SimpleRouter

from .documentations import (
    DecoratedShopperShippingAddressViewSet,
    decorated_issuing_token_view, decorated_refreshing_token_view, decorated_blacklisting_token_view,
    decorated_upload_business_registration_image_view, decorated_get_buildings_view, decorated_user_password_view,
    decorated_is_unique_view, decorated_product_like_view, decorated_shopper_point_history_view
)
from .views import CartViewSet

app_name = 'user'

router = SimpleRouter(trailing_slash=False)
router.register('/addresses', DecoratedShopperShippingAddressViewSet, basename='shipping-address')
router.register('/carts', CartViewSet, basename='cart')

token_urlpatterns = [
    path('', decorated_issuing_token_view),
    path('/refresh', decorated_refreshing_token_view),
    path('/blacklist', decorated_blacklisting_token_view),
]

shopper_url_patterns = [
    path('/<int:user_id>', include(router.urls)),
    path('/<int:user_id>/like/<int:product_id>', decorated_product_like_view),
    path('/<int:user_id>/point-histories', decorated_shopper_point_history_view)
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
    path('/shoppers', include(shopper_url_patterns))
]
