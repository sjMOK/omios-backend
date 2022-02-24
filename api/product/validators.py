import requests
from rest_framework.validators import ValidationError

from common.utils import BASE_IMAGE_URL


def validate_file_size(value):
    if value.size > 10485760:
        raise ValidationError("The maximum file size that can be uploaded is 10MB")
        

def validate_url(value):
    if not value.startswith(BASE_IMAGE_URL):
        raise ValidationError(detail='Enter a valid BASE_IMAGE_URL.')

    if not requests.get(value).status_code == 200:
        raise ValidationError(detail='object not found.')

    result = value.split(BASE_IMAGE_URL)
    value = result[-1]

    return value


def validate_price_difference(price, options):
    for option in options:
        price_difference = option.get('price_difference', 0)
        if price_difference > price * 0.2:
            raise ValidationError(
                'The option price difference must be less than 20% of the product price.'
            )
