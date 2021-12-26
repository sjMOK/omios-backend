from django.utils import timezone
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenViewBase
from . import models, serializers, permissions
from common.views import get_result_message


class TokenView(TokenViewBase):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        response.data = get_result_message(status.HTTP_201_CREATED, data=response.data)
        response.status_code = status.HTTP_201_CREATED
        return response


class UserBlacklistTokenView(TokenView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.TokenBlacklistSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        response.data['data'] = {'user_id': request.user.id}
        return response


class UserAccessTokenView(TokenView):
    serializer_class = serializers.UserAccessTokenSerializer


class UserRefreshTokenView(TokenView):
    serializer_class = serializers.UserRefreshTokenSerializer


class UserDetailView(APIView):
    permission_classes = [permissions.IsAuthenticatedExceptCreate]

    def __pop_user(self, data):
        if 'user' not in data.keys():
            return data

        user_data = data.pop('user')
        for key, value in user_data.items():
            data[key] = value

        return data

    def __push_user(self, data):
        user_keys = [field.name for field in models.User._meta.get_fields()]
        user_data = {}
        for key in user_keys:
            if key in data.keys():
                user_data[key] = data.pop(key)
        data['user'] = user_data

        return data

    def _get_model_instance(self, user):
        return user

    def get(self, request):
        serializer = self._serializer_class(instance=self._get_model_instance(request.user))

        data = self.__pop_user(serializer.data)
        data.pop('password')

        return Response(get_result_message(data=data))

    def post(self, request):
        data = self.__push_user(request.data)
        serializer = self._serializer_class(data=data)

        if not serializer.is_valid():
            return Response(get_result_message(status.HTTP_400_BAD_REQUEST, self.__pop_user(serializer.errors)), status=status.HTTP_400_BAD_REQUEST)
        
        user = serializer.save()
        
        return Response(get_result_message(status.HTTP_201_CREATED, data={'usre_id': user.user_id}), status=status.HTTP_201_CREATED)

    def patch(self, request):
        if 'password' in request.data:
            return Response(get_result_message(status.HTTP_400_BAD_REQUEST, 'password modification is not allowed in PATCH method'), status=status.HTTP_400_BAD_REQUEST)
        
        data = self.__push_user(request.data)
        serializer = self._serializer_class(instance=self._get_model_instance(request.user), data=data, partial=True)

        if not serializer.is_valid():
            return Response(get_result_message(status.HTTP_400_BAD_REQUEST, self.__pop_user(serializer.errors)), status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()

        return Response(get_result_message(data={'user_id': user.user_id}))

    def delete(self, request):
        user = request.user
        user.is_active = False
        user.save()

        return Response(get_result_message(data={'user_id': user.id}), status=status.HTTP_200_OK)


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
        data = request.data
    
        serializer = serializers.UserPasswordSerializer(data=data, user=user)
        if not serializer.is_valid():
            return Response(get_result_message(status.HTTP_400_BAD_REQUEST, serializer.errors), status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.last_update_password = timezone.now()
        user.save()
        self.__discard_refresh_token_by_user_id(user.id)

        return Response(get_result_message(data={'user_id': user.id}), status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def is_unique_username(request, username):
    if models.User.objects.filter(username=username).exists():
        return Response(get_result_message(data={'is_unique': False}), status=status.HTTP_200_OK)
    return Response(get_result_message(data={'is_unique': True}), status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def is_unique_nickname(request, nickname):
    if models.Shopper.objects.filter(nickname=nickname).exists():
        return Response(get_result_message(data={'is_unique': False}), status=status.HTTP_200_OK)
    return Response(get_result_message(data={'is_unique': True}), status=status.HTTP_200_OK)
