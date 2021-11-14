from django.urls import path, include
from. import views

app_name = 'member'

urlpatterns = [
    path('shopper/<int:pk>', views.ShopperDetailView.as_view()),
    path('shopper/signup/', views.shopper_signup),
    path('wholesaler/signup/', views.wholesaler_signup),
    # path('', views.index),
    # path('create_user/', views.create_user),
    # path('jwt_test/', views.jwt_test, name='jwt_test'),
    # path('token2/', views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('token/refresh/', views.TokenRefreshView.as_view(), name='token_refresh'),
    # path('custom_token/', views.UserAccessTokenView.as_view(), name='token_obtain_pair'),
    # path('custom_token/refresh/', views.UserRefreshTokenView.as_view(), name='token_refresh'),
    # path('test/', views.jwt_test2),

    path('token/', views.UserAccessTokenView.as_view(), name='access_token'),
    path('token/refresh/', views.UserRefreshTokenView.as_view(), name='refresh_token'),
    path('token/blacklist/', views.TokenBlacklistView.as_view(), name='token_blacklist'),
]