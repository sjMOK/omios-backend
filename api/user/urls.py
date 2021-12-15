from django.urls import path
from. import views

# app_name = 'user'

urlpatterns = [
    path('token/', views.UserAccessTokenView.as_view()),
    path('token/refresh/', views.UserRefreshTokenView.as_view()),
    path('token/blacklist/', views.TokenBlacklistView.as_view()),
    path('shopper/signup/', views.ShopperSignUpView.as_view()),
    path('wholesaler/signup/', views.WholesalerSignUpView.as_view()),
    path('shopper/', views.ShopperDetailView.as_view()),
    path('wholesaler/', views.WholesalerDetailView.as_view()),
    path('password/', views.UserPasswordView.as_view()),
]