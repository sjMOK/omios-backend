from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView

from . import models, serializers, permissions

result = {
    'code': 200,
    'id': '',
    'message': 'success', 
}

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


@api_view(['POST'])
def user_signup(request):
    from datetime import date
    request.data['birthday'] = date.today()

    data = push_user(request.data)
    serializer = serializers.ShopperSerializer(data=data)
    
    if serializer.is_valid():
        shopper = serializer.save()
        result['id']= shopper.user_id
    else:
        result['code'] = 400
        result['message'] = pop_user(serializer.errors)
        
        return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(result)

class ShopperDetailView(APIView):
    permission_classes = [permissions.IsOwnerInDetailView]

    def get_object(self, **kwargs):
        shopper = models.Shopper.objects.get(**kwargs)
        self.check_object_permissions(self.request, shopper)
        return shopper

    def get(self, request, id):
        # shopper = models.Shopper.objects.get(user_id=id)
        shopper = self.get_object(user_id=pk) 
        serializer = serializers.ShopperSerializer(instance=shopper)

        data = pop_user(serializer.data)
        data.pop('password')

        return Response(data)

    def patch(self, request, id):
        data = push_user(request.data)
        shopper = models.Shopper.objects.get(user_id=id)
        serializer = serializers.ShopperSerializer(instance=shopper, data=data, partial=True)
        
        if serializer.is_valid():
            shopper = serializer.save()
            result['id']= shopper.user_id   
        else:
            result['code'] = 400
            result['message'] = pop_user(serializer.errors)

            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result)

    def delete(self, request, id):
        user = models.User.objects.get(id=id)
        user.is_active = False
        user.save()
        return Response('username <{0}> user deleted'.format(user.username))
