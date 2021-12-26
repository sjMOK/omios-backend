from django.urls import path
from. import views

app_name = 'product'

urlpatterns = [
    path('smallcategory/', views.register_smallcategory),
]