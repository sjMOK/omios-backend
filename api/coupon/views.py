from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin

from common.permissions import IsAuthenticatedShopper
from common.utils import get_response
from .models import Coupon
from .serializers import CouponSerializer


class CouponViewSet(ListModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticatedShopper]
    serializer_class = CouponSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'cart_id'
    lookup_value_regex = r'[0-9]+'

    def get_queryset(self):
        qeuryset = Coupon.objects.all()

        if self.action == 'list': 
            queryset = qeuryset.filter(is_auto_issue=False)

        return queryset

    def create(self, requset):
        return get_response(data='coupon create')
