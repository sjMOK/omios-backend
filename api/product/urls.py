from django.urls import path
from rest_framework.routers import SimpleRouter
from . import views

app_name = 'product'

router = SimpleRouter()
router.register(r'', views.ProductViewSet, basename='product')

urlpatterns = [

]

urlpatterns += router.urls

category_urlpatterns = [
    path('', views.get_categories),
    path('<int:pk>/subcategory/', views.get_sub_categories),
]
