DEFAULT_IMAGE_URL = 'https://deepy.s3.ap-northeast-2.amazonaws.com/media/product/default.png'
BASE_IMAGE_URL= 'https://deepy.s3.ap-northeast-2.amazonaws.com/media/'

FREEZE_TIME = '2021-11-20 01:02:03.456789'
FREEZE_TIME_FORMAT = '%Y-%m-%d %H:%M:%S.%f'
FREEZE_TIME_AUTO_TICK_SECONDS = 10

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


def gmt_to_kst(gmt):
    from datetime import timedelta
    return gmt + timedelta(hours=9)