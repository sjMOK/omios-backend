from django.urls import path
from rest_framework.routers import SimpleRouter
from . import views

app_name = 'product'

router = SimpleRouter()
router.register(r'', views.ProductViewSet, basename='product')

urlpatterns = [
    path('main-category/', views.get_categories),
    path('main-category/<int:pk>/sub-category/', views.get_sub_categories),
    path('color/', views.get_colors),
]

urlpatterns += router.urls
