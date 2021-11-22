from django.urls import path
from. import views

# app_name = 'user'

urlpatterns = [
    path('token/', views.UserAccessTokenView.as_view(), name='access_token'),
    path('token/refresh/', views.UserRefreshTokenView.as_view(), name='refresh_token'),
    path('token/blacklist/', views.TokenBlacklistView.as_view(), name='token_blacklist'),
    path('shopper/', views.user_signup),
    path('shopper/<int:id>/', views.ShopperDetailView.as_view()),
    path('wholesaler/', views.user_signup),
]