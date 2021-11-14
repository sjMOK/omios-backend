from django.urls import path
from. import views

# app_name = 'user'

urlpatterns = [
    path('token/', views.UserAccessTokenView.as_view(), name='access_token'),
    path('token/refresh/', views.UserRefreshTokenView.as_view(), name='refresh_token'),
    path('token/blacklist/', views.TokenBlacklistView.as_view(), name='token_blacklist'),
    path('shopper/<int:pk>/', views.ShopperDetailView.as_view()),
    path('shopper/signup/', views.shopper_signup),
    path('wholesaler/signup/', views.wholesaler_signup),
]