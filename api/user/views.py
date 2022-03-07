from django.db.models.query import Prefetch

from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenViewBase

from common.utils import get_response, get_response_body
from common.views import upload_image_view
from .models import User, Shopper, Wholesaler, Building
from .serializers import (
    IssuingTokenSerializer, RefreshingTokenSerializer, TokenBlacklistSerializer,
    UserPasswordSerializer, ShopperSerializer, WholesalerSerializer, BuildingSerializer
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


class UserView(APIView):
    permission_classes = [IsAuthenticatedExceptCreate]

    def _get_model_instance(self, user):
        return user

    def get(self, request):
        serializer = self._serializer_class(instance=self._get_model_instance(request.user))

        return get_response(data=serializer.data)

    def post(self, request):
        serializer = self._serializer_class(data=request.data)
        if not serializer.is_valid():
            return get_response(status=HTTP_400_BAD_REQUEST, message=serializer.errors)
        
        user = serializer.save()

        return get_response(status=HTTP_201_CREATED, data={'id': user.user_id})

    def patch(self, request):
        if set(request.data).difference(self._patchable_fields):
            return get_response(status=HTTP_400_BAD_REQUEST, message='It contains requests for fields that do not exist or cannot be modified.')

        serializer = self._serializer_class(instance=self._get_model_instance(request.user), data=request.data, partial=True)
        if not serializer.is_valid():
            return get_response(status=HTTP_400_BAD_REQUEST, message=serializer.errors)

        serializer.save()

        return get_response(data={'id': request.user.id})

    def delete(self, request):
        user = request.user
        user.is_active = False
        user.save(update_fields=['is_active'])

        return get_response(data={'id': user.id})


class ShopperView(UserView):
    _serializer_class = ShopperSerializer
    _patchable_fields = set(['email', 'nickname', 'height', 'weight'])

    def _get_model_instance(self, user):
        return user.shopper


class WholesalerView(UserView):
    _serializer_class = WholesalerSerializer
    _patchable_fields = ['mobile_number', 'email']

    def _get_model_instance(self, user):
        return user.wholesaler


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
