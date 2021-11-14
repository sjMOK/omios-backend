from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import models, serializers
class UserAccessTokenView(TokenObtainPairView):
    serializer_class = serializers.UserAccessTokenSerializer

class UserRefreshTokenView(TokenRefreshView):
    serializer_class = serializers.UserRefreshTokenSerializer

@api_view(['POST'])
def shopper_signup(request):
    '''
    {
        "name": "권형석",
        "age": 25,
        "member": {
            "username": "kwon",
            "password": "kwon"
        }
    }
    '''
    serializer = serializers.ShopperSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    shopper = serializer.save()

    return Response('<<name: {0}, username: {1}>> shopper created'.format(shopper.name, shopper.member.username))

@api_view(['POST'])
def wholesaler_signup(request):
    '''
    {
        "name": "나는도매",
        "member": {
            "username": "im-domae",
            "password": "im_domae"
        }
    }
    '''
    serializer = serializers.WholesalerSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    wholesaler = serializer.save()

    return Response('<<company name: {0}, username: {1} wholesaler>> created'.format(wholesaler.name, wholesaler.member.username ))

@api_view(['GET', 'DELETE'])
def shopper(request, pk):
    member = models.Member.objects.get(id=pk)
    shopper = member.shopper
    
    if request.method == 'DELETE':
        shopper.delete()
        return Response('username <{0}> user deleted'.format(member.username))

    serializer = serializers.ShopperSerializer(instance=shopper)
    shopper_data = serializer.data
    shopper_data.pop('member')

    return Response(shopper_data)


class ShopperDetailView(APIView):
    def get(self, request, pk, format=None):
        # username = request.query_params.get('username')
        # member = Member.objects.get(username=username)

        # shopper = member.shopper
        # serializer = ShopperSerializer(instance=shopper)
        # return Response(serializer.data)

        member = models.Member.objects.get(id=pk)
        return Response(member.username)


    def post(self, request, format=None):
        # sign-up
        '''
        {
            "name": "권형석",
            "age": 25,
            "member": {
                "username": "kwon",
                "password": "kwon"
            }
        }
        '''
        serializer = serializers.ShopperSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member = serializer.save()
        return Response('username: {0}, name: {1} created'.format(member.username, member.shopper.name))

    def delete(self, request, format=None):
        username = request.query_params.get('username')
        member = models.Member.objects.get(username=username)
        member.delete()
        return Response('username <{0}> user deleted'.format(username))




