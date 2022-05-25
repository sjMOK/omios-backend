from datetime import date, datetime, timedelta
import re

from django.http import JsonResponse

from rest_framework.response import Response
from rest_framework.exceptions import APIException


DEFAULT_IMAGE_URL = 'https://deepy.s3.ap-northeast-2.amazonaws.com/media/product/default.png'
BASE_IMAGE_URL= 'https://deepy.s3.ap-northeast-2.amazonaws.com/media/'


def get_response_body(code, message='success', data=None):
    if int(code / 100) == 2:
        if message != 'success':
            raise APIException('Success response must contain "success" message.')
        elif data is None:
            raise APIException('Success response must contain data.')
    else:
        if message == 'success':
            raise APIException('Failure response must not contain "success" message.')
        elif data is not None:
            raise APIException('Failure response must not contain data.')

    result = {
        'code': code,
        'message': message, 
    }

    if data is not None:
        result['data'] = data

    return result


def get_response(type='drf', status=200, **kwargs):
    response_class = None
    if type == 'django':
        response_class = JsonResponse
    elif type == 'drf':
        response_class = Response

    return response_class(get_response_body(code=status, **kwargs), status=status)


def querydict_to_dict(querydict):
    data = {}
    for key in querydict.keys():
        value = querydict.getlist(key)
        if len(value) == 1:
            value = value[0]
        data[key] = value

    return data


def gmt_to_kst(gmt):
    return gmt + timedelta(hours=9)


def datetime_to_iso(datetime_instance):
    return datetime_instance.isoformat() if isinstance(datetime_instance, datetime) or isinstance(datetime_instance, date) else None


def levenshtein(a_text, b_text): 
    a_len = len(a_text) + 1 
    b_len = len(b_text) + 1 
    array = [ [] for a in range(a_len) ] 

    for i in range(a_len): 
        array[i] = [0 for _ in range(b_len)] 

    for i in range(b_len):
        array[0][i] = i 
    
    for i in range(a_len): 
        array[i][0] = i 

    cost = 0 
    for i in range(1, a_len): 
        for j in range(1, b_len): 
            if a_text[i-1] != b_text[j-1]: 
                cost = 1 
            else : 
                cost = 0 

            addNum = array[i-1][j] + 1 
            minusNum = array[i][j-1] + 1 
            modiNum = array[i-1][j-1] + cost 
            minNum = min([addNum, minusNum, modiNum]) 

            array[i][j] = minNum 
            
    return array[a_len-1][b_len-1]


def check_integer_format(value):
    if isinstance(value, str):
        value = [value]

    p = re.compile(r'^[0-9]+$')
    for v in value:
        if not p.match(v):
            return False

    return True
