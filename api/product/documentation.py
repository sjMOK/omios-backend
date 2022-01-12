from rest_framework.serializers import *
from drf_yasg.utils import swagger_auto_schema
from django.utils.decorators import method_decorator

from common import documentation
from . import models, serializers, views

class MainCategory(serializers.MainCategorySerializer):
    pass


class SubCategory(serializers.SubCategorySerializer):
    pass


class SubCategoryResponse(Serializer):
    main_category_id = IntegerField()
    sub_category = SubCategory(many=True)


class Color(serializers.ColorSerializer):
    pass


decorated_main_category_view = swagger_auto_schema(
    method='GET', **documentation.get_response(MainCategory(many=True)), security=[], operation_description='상품 메인 카테고리 가져오기'
)(views.get_main_categories)

decorated_sub_category_view = swagger_auto_schema(
    method='GET', **documentation.get_response(SubCategoryResponse()), security=[], operation_description='상품 서브 카테고리 가져오기'
)(views.get_sub_categories)

decorated_color_view = swagger_auto_schema(
    method='GET', **documentation.get_response(Color(many=True)), security=[], operation_description='상품 색상 가져오기'
)(views.get_colors)
