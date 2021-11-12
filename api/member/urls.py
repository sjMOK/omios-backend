from django.urls import path
from . import views


urlpatterns = [
    path('', views.index),
    path('create_user/', views.create_user),
    path('jwt_test/', views.jwt_test, name='jwt_test'),
    path('token/', views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', views.TokenRefreshView.as_view(), name='token_refresh'),
    path('custom_token/', views.UserAccessTokenView.as_view(), name='token_obtain_pair'),
    path('custom_token/refresh/', views.UserRefreshTokenView.as_view(), name='token_refresh'),
    path('test/', views.jwt_test2),
]