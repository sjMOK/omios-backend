from django.urls import path, include
from. import views

app_name = 'member'

urlpatterns = [
    path('shopper/<int:pk>', views.ShopperDetailView.as_view()),
    path('shopper/signup/', views.shopper_signup),
    path('wholesaler/signup/', views.wholesaler_signup)
]