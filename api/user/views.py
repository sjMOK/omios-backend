from django.db.models.query import Prefetch
from django.shortcuts import get_object_or_404
from django.db import connection

from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenViewBase

from common.utils import get_response, get_response_body, check_id_format
from common.views import upload_image_view
from product.models import Product
from .models import ShopperShippingAddress, User, Shopper, Wholesaler, Building, ProductLike
from .serializers import (
    IssuingTokenSerializer, RefreshingTokenSerializer, TokenBlacklistSerializer,
    UserPasswordSerializer, ShopperSerializer, WholesalerSerializer, BuildingSerializer,
    ShopperShippingAddressSerializer,
)
from .permissions import AllowAny, IsAuthenticated, IsAuthenticatedExceptCreate


class TokenView(TokenViewBase):
    def post(self, request, *args, **kwargs):
        return get_response(status=HTTP_201_CREATED, data=super().post(request, *args, **kwargs).data)


class IssuingTokenView(TokenView):
    serializer_class = IssuingTokenSerializer


class RefreshingTokenView(TokenView):
    serializer_class = RefreshingTokenSerializer


class BlacklistingTokenView(TokenView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = TokenBlacklistSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        response.data = get_response_body(response.status_code, data={'id': request.user.id})
        return response


class UserViewSet(GenericViewSet):
    permission_classes = [IsAuthenticatedExceptCreate]
    lookup_field = 'user_id'
    lookup_value_regex = r'[0-9]+'

    def retrieve(self, request, user_id=None):
        user = self.get_object()
        serializer = self.get_serializer(instance=user)

        return get_response(data=serializer.data)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return get_response(status=HTTP_400_BAD_REQUEST, message=serializer.errors)
        
        user = serializer.save()

        return get_response(status=HTTP_201_CREATED, data={'id': user.user_id})

    def partial_update(self, request, user_id=None):
        if set(request.data).difference(self._patchable_fields):
            return get_response(status=HTTP_400_BAD_REQUEST, message='It contains requests for fields that do not exist or cannot be modified.')
        
        user = self.get_object()
        serializer = self.get_serializer(instance=user, data=request.data, partial=True)
        if not serializer.is_valid():
            return get_response(status=HTTP_400_BAD_REQUEST, message=serializer.errors)

        serializer.save()

        return get_response(data={'id': request.user.id})

    def destroy(self, request, user_id=None):
        user = self.get_object()
        user.delete()

        return get_response(data={'id': user.id})


class ShopperViewSet(UserViewSet):
    serializer_class = ShopperSerializer
    _patchable_fields = set(['email', 'nickname', 'height', 'weight'])

    def get_queryset(self):
        return Shopper.objects.filter(is_active=True)


class WholesalerViewSet(UserViewSet):
    serializer_class = WholesalerSerializer
    _patchable_fields = ['mobile_number', 'email']

    def get_queryset(self):
        return Wholesaler.objects.filter(is_active=True)


@api_view(['POST'])
@permission_classes([AllowAny])
def upload_business_registration_image(request):
    return upload_image_view(request, 'business_registration')


@api_view(['GET'])
@permission_classes([AllowAny])
def get_buildings(request):
    serializer = BuildingSerializer(instance=Building.objects.all().prefetch_related(Prefetch('floors')), many=True)

    return get_response(data=serializer.data)


@api_view(['PATCH'])
def change_password(request):    
    serializer = UserPasswordSerializer(instance=request.user, data=request.data)
    if not serializer.is_valid():
        return get_response(status=HTTP_400_BAD_REQUEST, message=serializer.errors)

    serializer.save()
    
    return get_response(data={'id': request.user.id})


@api_view(['GET'])
@permission_classes([AllowAny])
def is_unique(request):
    mapping = {
        'username': {'model': User, 'column': 'username'},
        'shopper_nickname': {'model': Shopper, 'column': 'nickname'},
        'wholesaler_name': {'model': Wholesaler, 'column': 'name'},
        'wholesaler_company_registration_number': {'model': Wholesaler, 'column': 'company_registration_number'},
    }

    request_data = list(request.query_params.items())
    if len(request.query_params) != 1:
        return get_response(status=HTTP_400_BAD_REQUEST, message='Only one parameter is allowed.')
    elif request_data[0][0] not in mapping.keys():
        return get_response(status=HTTP_400_BAD_REQUEST, message='Invalid parameter name.')

    mapping_data = mapping[request_data[0][0]]
    if mapping_data['model'].objects.filter(**{mapping_data['column']: request_data[0][1]}).exists():
        return get_response(data={'is_unique': False})

    return get_response(data={'is_unique': True})


class ProductLikeView(APIView):
    def get_queryset(self):
        return ProductLike.objects.all()

    def post(self, request, user_id, product_id):
        shopper = get_object_or_404(Shopper, id=user_id)
        product = get_object_or_404(Product, id=product_id)

        if self.get_queryset().filter(shopper=shopper, product=product).exists():
            return get_response(status=HTTP_400_BAD_REQUEST, message='Duplicated user and product')

        ProductLike.objects.create(shopper=shopper, product=product)
        return get_response(status=HTTP_201_CREATED, data={'shopper_id': user_id, 'product_id': product.id})

    def delete(self, request, user_id, product_id):
        shopper = get_object_or_404(Shopper, id=user_id)
        product = get_object_or_404(Product, id=product_id)

        if not self.get_queryset().filter(shopper=shopper, product=product).exists():
            return get_response(status=HTTP_400_BAD_REQUEST, message='You are deleting non exist likes')

        product_like = ProductLike.objects.get(shopper=shopper, product=product)
        product_like.delete()

        return get_response(data={'shopper_id': user_id, 'product_id': product_id})


class ShopperShippingAddressViewSet(GenericViewSet):
    serializer_class = ShopperShippingAddressSerializer
    lookup_url_kwarg = 'shipping_address_id'
    lookup_value_regex = r'[0-9]+'

    def get_queryset(self):
        return self.request.user.shopper.addresses.all()

    def list(self, request, user_id):
        serializer = self.get_serializer(instance=self.get_queryset(), many=True)

        return get_response(data=serializer.data)

    def create(self, request, user_id):
        serializer = self.get_serializer(data=request.data, context={'shopper': request.user.shopper})

        if not serializer.is_valid():
            return get_response(status=HTTP_400_BAD_REQUEST, message=serializer.errors)

        shipping_address = serializer.save()

        return get_response(status=HTTP_201_CREATED, data={'id': shipping_address.id})

    def partial_update(self, request, user_id, shipping_address_id):
        shipping_address = self.get_object()
        serializer = self.get_serializer(
            instance=shipping_address, data=request.data, partial=True, context={'shopper': request.user.shopper}
        )
        
        if not serializer.is_valid():
            return get_response(status=HTTP_400_BAD_REQUEST, message=serializer.errors)

        shipping_address = serializer.save()

        return get_response(data={'id': shipping_address.id})

    def destroy(self, request, user_id, shipping_address_id):
        shipping_address = self.get_object()
        shipping_address.delete()

        return get_response(data={'id': int(shipping_address_id)})

    @action(methods=['GET'], detail=False, url_path='default')
    def get_default_address(self, request, user_id):
        queryset = self.get_queryset()

        if not queryset.exists():
            return get_response(data={})
        elif queryset.filter(is_default=True).exists():
            try:
                shipping_address = queryset.get(is_default=True)
            except ShopperShippingAddress.MultipleObjectsReturned:
                shipping_address = queryset.filter(is_default=True).last()
        else:
            shipping_address = queryset.last()

        serializer = self.get_serializer(shipping_address)

        return get_response(data=serializer.data)
