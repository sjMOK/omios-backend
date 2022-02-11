from rest_framework.views import exception_handler

from .utils import get_response, get_response_body


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
    
    response.data = get_response_body(response.status_code, message)
    return response


def custom_404_view(request, exception):
    return get_response('django', 404, message='Page Not Found, please check url.')


def custom_500_view(request):
    return get_response('django', 500, message='Server Error.')
