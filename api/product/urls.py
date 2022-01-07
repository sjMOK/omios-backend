from django.urls import path
from. import views

app_name = 'product'

urlpatterns = [
    
]

category_urlpatterns = [
    path('', views.get_categories),
    path('<int:pk>/', views.get_category_info),
]
