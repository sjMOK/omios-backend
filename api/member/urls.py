from django.urls import path, include
from. import views

app_name = 'member'

urlpatterns = [
    path('shopper/signup/', views.shopper_signup),
    path('shopper/', views.shopper),
    path('wholesaler/signup/', views.wholesaler_signup)
]