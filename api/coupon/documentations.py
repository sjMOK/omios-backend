from django.db import transaction

from drf_yasg.utils import swagger_auto_schema
from rest_framework.serializers import Serializer, BooleanField, IntegerField, URLField

from common.documentations import get_response
from .views import CouponViewSet, get_coupon_classifications
from .serializers import CouponClassificationSerializer, CouponSerializer


class CouponResponse(Serializer):
    class CouponResultsResponse(CouponSerializer):
        coupon_owned = BooleanField()

    count = IntegerField()
    next = URLField()
    previous = URLField()
    results = CouponResultsResponse(many=True)
    


class DecoratedCouponViewSet(CouponViewSet):
    list_discription = '''쿠폰 리스트 조회
    Admin user는 발행된 모든 쿠폰 조회 가능
    Shopper 혹은 익명 user는 발행된 쿠폰 중 발급받을 수 있는 쿠폰만 조회 가능
    Wholesaler는 permission denied
    \ncoupon_owned: Shopper가 해당 쿠폰을 가지고 있는지 여부 데이터(Admin user와 익명 user는 항상 false)
    '''

    create_discription = '''쿠폰 생성
    Admin user만 생성 가능
    discount_rate(할인율)와 discount_price(할인가) 둘 중 하나만 전송
    (start_date, end_date)와 available_period(사용 기한) 둘 중 하나만 전송
    end_date(만료 일자)는 start_date(시작 일자)보다 나중의 일자여야 함
    end_date는 전송하는 시점보다 나중의 일자여야 함
    \n일부 상품 쿠폰(classification=2)의 경우 products를 반드시 넘겨야 하며 최대 개수는 1000개
    카테고리별 쿠폰(classification=3)의 경우 sub_categories를 반드시 넘겨야 하며 최대 개수는 20개
    '''

    @swagger_auto_schema(**get_response(CouponResponse(many=True)), operation_description=list_discription)
    def list(self, *args, **kwargs):
        return super().list(*args, **kwargs)

    @swagger_auto_schema(request_body=CouponSerializer, **get_response(code=201),operation_description=create_discription)
    def create(self, *args, **kwargs):
        return super().create(*args, **kwargs)


decorated_get_coupon_classifications_view = swagger_auto_schema(
    method='GET', **get_response(CouponClassificationSerializer(many=True)), security=[], operation_description='쿠폰 분류 리스트 조회'
)(get_coupon_classifications)
