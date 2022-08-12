from django.urls import path

from rest_framework.routers import SimpleRouter

from .documentations import (
    DecoratedProductQuestionAnswerViewSet,
    decorated_get_all_categories_view, decorated_get_main_categories_view, decorated_get_sub_categories_by_main_category_view,
    decorated_get_colors_view, decorated_get_tag_search_result_view, decorated_upload_product_image_view,
    decorated_get_related_search_words_view, decorated_get_product_question_answer_classification,
    decorated_get_product_registration_data_view,
)


app_name = 'product'

router = SimpleRouter(trailing_slash=False)
router.register(r'/(?P<product_id>\d+)/question-answers', DecoratedProductQuestionAnswerViewSet, 'question-answer')

urlpatterns = [
    path('/categories', decorated_get_all_categories_view),
    path('/main-categories', decorated_get_main_categories_view),
    path('/main-categories/<int:id>/sub-categories', decorated_get_sub_categories_by_main_category_view),
    path('/colors', decorated_get_colors_view),
    path('/tags', decorated_get_tag_search_result_view),
    path('/images', decorated_upload_product_image_view),
    path('/related-search-words', decorated_get_related_search_words_view),
    path('/question-answers/classifications', decorated_get_product_question_answer_classification),
    path('/registration-datas', decorated_get_product_registration_data_view),
]

urlpatterns += router.urls
