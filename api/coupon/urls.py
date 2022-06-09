from django.urls import path, include

from .views import get_coupon_classifications


app_name = 'coupon'

urlpatterns = [
    path('/classifications', get_coupon_classifications),
]
