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
