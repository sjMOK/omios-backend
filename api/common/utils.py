import base64
from django.core.files.base import ContentFile

def get_result_message(code=200, message='success', data=None):
    result = {
        'code': code,
        'message': message, 
    }
    if data and int(code / 100) == 2:
        result['data'] = data

    return result

def querydict_to_dict(querydict):
    data = {}
    for key in querydict.keys():
        value = querydict.getlist(key)
        if len(value) == 1:
            value = value[0]
        data[key] = value

    return data


def base64_to_imgfile(raw_base64):
    try:
        format, imgstr = raw_base64.split(';base64,')
        _name, ext = format.split('/')
        name = '{0}.{1}'.format(_name.split(':')[-1], ext)
        imgfile = ContentFile(base64.b64decode(imgstr), name=name)
        return imgfile
    except:
        return False
