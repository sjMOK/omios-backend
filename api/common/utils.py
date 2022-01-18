import base64

from django.core.files.base import ContentFile

from rest_framework.views import exception_handler
from user.models import User

def get_result_message(code=200, message='success', data=None):
    result = {
        'code': code,
        'message': message, 
    }
    if data:
        result['data'] = data

    return result


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response

    data = {'code': response.status_code}
    if isinstance(response.data, dict):
        if 'detail' in response.data:
            data['message'] = response.data['detail']
        else:
            data['message'] = response.data
    elif isinstance(response.data, list):
        data['message'] = response.data
    
    response.data = data    
    return response


def querydict_to_dict(querydict):
    data = {}
    for key in querydict.keys():
        value = querydict.getlist(key)
        if len(value) == 1:
            value = value[0]
        data[key] = value

    return data


def base64_to_imgfile(raw_base64):
    format, imgstr = raw_base64.split(';base64,')
    _name, ext = format.split('/')
    name = '{0}.{1}'.format(_name.split(':')[-1], ext)
    imgfile = ContentFile(base64.b64decode(imgstr), name=name)

    return imgfile
