import requests
from rest_framework.validators import ValidationError

from common.utils import BASE_IMAGE_URL
        

def validate_url(value):
    if not value.startswith(BASE_IMAGE_URL):
        raise ValidationError(detail='Enter a valid BASE_IMAGE_URL.')

    if not requests.get(value).status_code == 200:
        raise ValidationError(detail='Not found.')

    result = value.split(BASE_IMAGE_URL)
    value = result[-1]

    return value
