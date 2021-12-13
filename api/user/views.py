import re
from django.http.response import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView

from . import models, serializers, permissions

from django.forms.models import model_to_dict

def get_result_message(status=200, message='success'):
    result = {
        'code': status,
        'message': message, 
    }
    return result

def pop_user(data):
    user_data = data.pop('user')
    for key, value in user_data.items():
        data[key] = value

    return data

def push_user(data):
    user_keys = [field.name for field in models.User._meta.get_fields()]
    user_data = {}

    for key in user_keys:
        if key not in data.keys():
            continue

        value = data.pop(key)
        user_data[key] = value

    data['user'] = user_data
    return data


class UserAccessTokenView(TokenObtainPairView):
    serializer_class = serializers.UserAccessTokenSerializer


class UserRefreshTokenView(TokenRefreshView):
    serializer_class = serializers.UserRefreshTokenSerializer


@api_view(['PATCH'])
@permission_classes([permissions.IsOwnerInDetailView])
def change_password(request, id):
    try:
        user = get_object_or_404(models.User, id=id)
    except Http404:
        result = get_result_message(status=404, message='object not found')
        return Response(result, status=status.HTTP_404_NOT_FOUND)
    
    serializer = serializers.UserPasswordSerializer(data=request.data)

    if serializer.is_valid():
        pass
    else:
        result = get_result_message(status=400, message=serializer.errors)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)

    current_password = serializer.validated_data['current_password']
    new_password = serializer.validated_data['new_password']

    if current_password == new_password:
        result = get_result_message(status=400, 
                                    message='new password is same as the current password')
        return Response(result, status=status.HTTP_400_BAD_REQUEST)

    if not user.check_password(current_password):
        result = get_result_message(status=400, 
                                    message='current password does not correct')
        return Response(result, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()

    result = get_result_message(status=200)
    result['id'] = id

    return Response(result, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def user_signup(request):
    data = push_user(request.data)
    serializer = serializers.ShopperSerializer(data=data)
    
    if serializer.is_valid():
        shopper = serializer.save()
        result = get_result_message(status=200)
        result['id']= shopper.user_id
    else:
        result = get_result_message(status=400, message=serializer.errors)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(result)

class ShopperDetailView(APIView):
    permission_classes = [permissions.IsOwnerInDetailView]
    
    def get_object(self, **kwargs):
        shopper = get_object_or_404(models.Shopper, **kwargs)
        self.check_object_permissions(self.request, shopper)
        return shopper

    def get(self, request, id):
        try:
            shopper = self.get_object(user_id=id)
        except Http404:
            result = get_result_message(status=404, message='object not found')
            return Response(result, status=status.HTTP_404_NOT_FOUND)
            
        serializer = serializers.ShopperSerializer(instance=shopper)

        data = pop_user(serializer.data)
        data.pop('password')

        return Response(data)

    def patch(self, request, id):
        if 'password' in request.data:
            result = get_result_message(status=400, message='password modification is not allowed in PATCH method')
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        try:
            shopper = self.get_object(user_id=id)
        except Http404:
            result = get_result_message(status=404, message='object not found')
            return Response(result, status=status.HTTP_404_NOT_FOUND)

        data = push_user(request.data)
        serializer = serializers.ShopperSerializer(instance=shopper, data=data, partial=True)
        
        if serializer.is_valid():
            shopper = serializer.save()
            result = get_result_message(status=200)
            result['id']= shopper.user_id
        else:
            result = get_result_message(status=400, message=pop_user(serializer.errors))
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result)

    def delete(self, request, id):
        try:
            user = self.get_object(user_id=id).user
        except Http404:
            result = get_result_message(status=404, message='object not found')
            return Response(result, status=status.HTTP_404_NOT_FOUND)

        user.is_active = False
        user.save()

        result = get_result_message(status=200)
        result['id'] = id
        return Response(result, status=status.HTTP_200_OK)
