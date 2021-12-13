from django.urls import path
from. import views

# app_name = 'user'

urlpatterns = [
    path('token/', views.UserAccessTokenView.as_view()),
    path('token/refresh/', views.UserRefreshTokenView.as_view()),
    path('token/blacklist/', views.TokenBlacklistView.as_view()),
    path('shopper/', views.user_signup),
    path('shopper/<int:id>/', views.ShopperDetailView.as_view()),
    path('wholesaler/', views.user_signup),
    path('password/', views.UserPasswordView.as_view()),
    path('shopper2/<int:id>/', views.ShopperDetailView2.as_view()),
]