from django.http import JsonResponse
from django.views.defaults import page_not_found
from rest_framework import exceptions
from .utils import get_result_message

def custom_400_view(request, exception):
    return JsonResponse(get_result_message(400, '400 Bad Request !!!'), status=400)

def custom_403_view(request, exception):
    return JsonResponse(get_result_message(400, '403 Forbidden !!!'), status=403)    

def custom_404_view(request, exception):
    return JsonResponse(get_result_message(404, '404 Not Found !!!'), status=404)

def custom_500_view(request):
    return JsonResponse(get_result_message(500, '500 Server Error !!!'), status=500)

