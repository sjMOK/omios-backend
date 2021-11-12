from django.views import View
from django.views.generic import TemplateView
from rest_framework import serializers

from rest_framework.views import APIView
from rest_framework.generics import DestroyAPIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from member.serializers import MemberSerializer, ShopperSerializer, WholesalerSerializer

from .models import Member

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
    serializer = ShopperSerializer(data=request.data)
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
    serializer = WholesalerSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    wholesaler = serializer.save()

    return Response('<<company name: {0}, username: {1} wholesaler>> created'.format(wholesaler.name, wholesaler.member.username ))

@api_view(['GET', 'DELETE'])
def shopper(request):
    print(type(request))
    username = request.query_params.get('username')
    member = Member.objects.get(username=username)
    shopper = member.shopper
    
    if request.method == 'DELETE':
        shopper.delete()
        return Response('username <{0}> user deleted'.format(username))

    serializer = ShopperSerializer(instance=shopper)
    return Response(serializer.data)


class ShopperDetailView(APIView):
    def get(self, request, format=None):
        username = request.query_params.get('username')
        member = Member.objects.get(username=username)

        shopper = member.shopper
        serializer = ShopperSerializer(instance=shopper)
        return Response(serializer.data)

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
        serializer = ShopperSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member = serializer.save()
        return Response('username: {0}, name: {1} created'.format(member.username, member.shopper.name))

    def delete(self, request, format=None):
        username = request.query_params.get('username')
        member = Member.objects.get(username=username)
        member.delete()
        return Response('username <{0}> user deleted'.format(username))
