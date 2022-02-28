from rest_framework.views import exception_handler
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR

from .utils import get_response, get_response_body
from .serializers import ImageSerializer
from .storage import upload_images


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
    return get_response('django', HTTP_404_NOT_FOUND, message='Page Not Found, please check url.')


def custom_500_view(request):
    return get_response('django', HTTP_500_INTERNAL_SERVER_ERROR, message='Server Error.')


def upload_image_view(request, type, *args):
    images = request.FILES.getlist('image')

    serializer = ImageSerializer(data=[{'image': image} for image in images], many=True)
    if not serializer.is_valid():
        return get_response(status=HTTP_400_BAD_REQUEST, message=serializer.errors)

    return get_response(status=HTTP_201_CREATED, data={'image': upload_images(type, images, *args)})