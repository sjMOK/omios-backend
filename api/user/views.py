from django.utils import timezone
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework_simplejwt.views import TokenViewBase

from common.utils import get_response, get_response_body
from . import models, serializers, permissions


class TokenView(TokenViewBase):
    def post(self, request, *args, **kwargs):
        return get_response(status=HTTP_201_CREATED, data=super().post(request, *args, **kwargs).data)


class UserBlacklistTokenView(TokenView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.TokenBlacklistSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        response.data = get_response_body(response.status_code, data={'id': request.user.id})
        return response


class UserAccessTokenView(TokenView):
    serializer_class = serializers.UserAccessTokenSerializer


class UserRefreshTokenView(TokenView):
    serializer_class = serializers.UserRefreshTokenSerializer


class UserDetailView(APIView):
    permission_classes = [permissions.IsAuthenticatedExceptCreate]

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
        if 'password' in request.data:
            return get_response(status=HTTP_400_BAD_REQUEST, message='password modification is not allowed in PATCH method')
        
        serializer = self._serializer_class(instance=self._get_model_instance(request.user), data=request.data, partial=True)

        if not serializer.is_valid():
            return get_response(status=HTTP_400_BAD_REQUEST, message=serializer.errors)

        user = serializer.save()

        return get_response(data={'id': user.user_id})

    def delete(self, request):
        user = request.user
        user.is_active = False
        user.save()

        return get_response(data={'id': user.id})


class ShopperDetailView(UserDetailView):
    _serializer_class = serializers.ShopperSerializer

    def _get_model_instance(self, user):
        return user.shopper


class WholesalerDetailView(UserDetailView):
    _serializer_class = serializers.WholesalerSerializer

    def _get_model_instance(self, user):
        return user.wholesaler


class UserPasswordView(APIView):
    def __discard_refresh_token_by_user_id(self, user_id):
        all_tokens = models.OutstandingToken.objects.filter(user_id=user_id, expires_at__gt=timezone.now()).all()

        discarding_tokens = []
        for token in all_tokens:
            if not hasattr(token, 'blacklistedtoken'):
                discarding_tokens.append(models.BlacklistedToken(token=token))
    
        models.BlacklistedToken.objects.bulk_create(discarding_tokens)

    def patch(self, request):
        user = request.user
    
        serializer = serializers.UserPasswordSerializer(data=request.data, user=request.user)
        if not serializer.is_valid():
            return get_response(status=HTTP_400_BAD_REQUEST, message=serializer.errors)

        user.set_password(serializer.validated_data['new_password'])
        user.last_update_password = timezone.now()
        user.save()
        self.__discard_refresh_token_by_user_id(user.id)

        return get_response(data={'id': user.id})


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def is_unique(request):
    mapping = {
        'username': {'model': models.User, 'column': 'username'},
        'shopper_nickname': {'model': models.Shopper, 'column': 'nickname'},
        'wholesaler_name': {'model': models.Wholesaler, 'column': 'name'},
        'wholesaler_company_registration_number': {'model': models.Wholesaler, 'column': 'company_registration_number'},
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
