from django.http import JsonResponse
from rest_framework.views import exception_handler

from .utils import get_result_message

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response

    if isinstance(response.data, dict):
        if 'detail' in response.data:
            message = response.data['detail']
        else:
            message = response.data
    elif isinstance(response.data, list):
        message = response.data
    
    response.data = get_result_message(response.status_code, message)
    return response

def custom_400_view(request, exception):
    return JsonResponse(get_result_message(400, 'Bad Request'), status=400)

def custom_403_view(request, exception):
    return JsonResponse(get_result_message(400, 'Forbidden'), status=403)    

def custom_404_view(request, exception):
    return JsonResponse(get_result_message(404, 'Page Not Found, please check url'), status=404)

def custom_500_view(request):
    return JsonResponse(get_result_message(500, 'Server Error'), status=500)

