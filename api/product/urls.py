from django.urls import path
from rest_framework.routers import SimpleRouter
from . import views, documentation


app_name = 'product'

router = SimpleRouter()
router.register(r'', views.ProductViewSet, basename='product')

urlpatterns = [
    path('main-category/', documentation.decorated_main_category_view),
    path('main-category/<int:id>/sub-category/', documentation.decorated_sub_category_view),
    path('color/', documentation.decorated_color_view),
    path('image/', views.upload_prdocut_image),
    path('searchbox/', views.get_searchbox_data),
]

urlpatterns += router.urls
