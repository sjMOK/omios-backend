from django.urls import path

from rest_framework.routers import SimpleRouter

from .views import (
    ProductViewSet, get_all_categories, upload_prdocut_image, get_searchbox_data,
    get_common_registration_data, get_dynamic_registation_data,
)
from .documentation import (
    decorated_main_category_view, decorated_sub_category_view, decorated_color_view,
)


app_name = 'product'

router = SimpleRouter()
router.register(r'', ProductViewSet, basename='product')

urlpatterns = [
    path('category/', get_all_categories),
    path('main-category/', decorated_main_category_view),
    path('main-category/<int:id>/sub-category/', decorated_sub_category_view),
    path('color/', decorated_color_view),
    path('image/', upload_prdocut_image),
    path('searchbox/', get_searchbox_data),
    path('registry-common/', get_common_registration_data),
    path('registry-dynamic/', get_dynamic_registation_data),
]

urlpatterns += router.urls
