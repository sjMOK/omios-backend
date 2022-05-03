from rest_framework.validators import ValidationError

from common.models import TemporaryImage
from common.utils import BASE_IMAGE_URL


def validate_file_size(value):
    if value.size > 10485760:
        raise ValidationError("The maximum file size that can be uploaded is 10MB")


def validate_all_required_fields_included(attrs, fields):
    for key, value in fields.items():
        if getattr(value, 'required') and key not in attrs:
            raise ValidationError('{0} field is required.'.format(key))


def validate_image_url(image_url):
    # if not image_url.startswith(BASE_IMAGE_URL):
    #     raise ValidationError(detail='Enter a valid image url.')

    image_url = image_url.split(BASE_IMAGE_URL)[-1]   
    queryset = TemporaryImage.objects.filter(image_url=image_url)
    if not queryset.exists():
        raise ValidationError(detail='Not found.')
    else:
        queryset.delete()

    return image_url
