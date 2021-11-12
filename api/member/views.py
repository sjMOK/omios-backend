from django.http.response import HttpResponse
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView
from . import serializers
from django.contrib.auth.models import User
from rest_framework.renderers import JSONRenderer
from rest_framework.decorators import api_view, renderer_classes

from django.contrib.auth.backends import ModelBackend

class UserAccessTokenView(TokenObtainPairView):
    serializer_class = serializers.UserAccessTokenSerializer

class UserRefreshTokenView(TokenRefreshView):
    serializer_class = serializers.UserRefreshTokenSerializer

# Create your views here.
def index(request):
    return HttpResponse("aaa")

def create_user(request):
    user = User(username="aaa")
    user.set_password("bbb")
    user.save()

    return HttpResponse("success")

@api_view(('GET',))
# @renderer_classes((JSONRenderer))
def jwt_test(request):
    user = User.objects.all()
    serializer = serializers.UserSerializer(user, many=True)    
    return Response(serializer.data)

def jwt_test2(request):
    pass
