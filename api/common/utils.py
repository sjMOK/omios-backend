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
