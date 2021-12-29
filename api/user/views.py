from django.utils import timezone
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework_simplejwt.views import TokenViewBase

from common import utils
from . import models, serializers, permissions


class TokenView(TokenViewBase):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        response.data = utils.get_result_message(HTTP_201_CREATED, data=response.data)
        response.status_code = HTTP_201_CREATED
        return response


class UserBlacklistTokenView(TokenView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.TokenBlacklistSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        response.data['data'] = {'id': request.user.id}
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

        return Response(utils.get_result_message(data=serializer.data))

    def post(self, request):
        serializer = self._serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response(utils.get_result_message(HTTP_400_BAD_REQUEST, serializer.errors), status=HTTP_400_BAD_REQUEST)
        
        user = serializer.save()
        
        return Response(utils.get_result_message(HTTP_201_CREATED, data={'id': user.user_id}), status=HTTP_201_CREATED)

    def patch(self, request):
        if 'password' in request.data:
            return Response(utils.get_result_message(HTTP_400_BAD_REQUEST, 'password modification is not allowed in PATCH method'), status=HTTP_400_BAD_REQUEST)
        
        serializer = self._serializer_class(instance=self._get_model_instance(request.user), data=request.data, partial=True)

        if not serializer.is_valid():
            return Response(utils.get_result_message(HTTP_400_BAD_REQUEST, self.serializer.errors), status=HTTP_400_BAD_REQUEST)

        user = serializer.save()

        return Response(utils.get_result_message(data={'id': user.user_id}))

    def delete(self, request):
        user = request.user
        user.is_active = False
        user.save()

        return Response(utils.get_result_message(data={'id': user.id}), status=HTTP_200_OK)


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
            return Response(utils.get_result_message(HTTP_400_BAD_REQUEST, serializer.errors), status=HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.last_update_password = timezone.now()
        user.save()
        self.__discard_refresh_token_by_user_id(user.id)

        return Response(utils.get_result_message(data={'id': user.id}), status=HTTP_200_OK)


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
        return Response(utils.get_result_message(HTTP_400_BAD_REQUEST, 'Only one parameter is allowed.'), status=HTTP_400_BAD_REQUEST)
    elif request_data[0][0] not in mapping.keys():
        return Response(utils.get_result_message(HTTP_400_BAD_REQUEST, 'Invalid parameter name.'), status=HTTP_400_BAD_REQUEST)

    mapping_data = mapping[request_data[0][0]]
    if mapping_data['model'].objects.filter(**{mapping_data['column']: request_data[0][1]}).exists():
        return Response(utils.get_result_message(data={'is_unique': False}), status=HTTP_200_OK)

    return Response(utils.get_result_message(data={'is_unique': True}), status=HTTP_200_OK)
