from django.urls import path

from .documentation import (
    decorated_get_all_categories_view, decorated_get_main_categories_view, decorated_sub_category_view,
    decorated_get_colors_view, decorated_get_tag_search_result_view, decorated_upload_product_image_view,
    decorated_get_related_search_words_view, decorated_get_common_registration_data_view, 
    decorated_get_dynamic_registration_data_view,
)

app_name = 'product'

urlpatterns = [
    path('/categories', decorated_get_all_categories_view),
    path('/main-categories', decorated_get_main_categories_view),
    path('/main-categories/<int:id>/sub-categories', decorated_sub_category_view),
    path('/colors', decorated_get_colors_view),
    path('/tags', decorated_get_tag_search_result_view),
    path('/images', decorated_upload_product_image_view),
    path('/related-search-words', decorated_get_related_search_words_view),
    path('/registry-common', decorated_get_common_registration_data_view),
    path('/registry-dynamic', decorated_get_dynamic_registration_data_view),
]
