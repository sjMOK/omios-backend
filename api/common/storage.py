import os

from django.utils import timezone
from rest_framework.exceptions import APIException, ValidationError

from storages.backends.s3boto3 import S3Boto3Storage

from .utils import IMAGE_DATETIME_FORMAT
from .models import TemporaryImage


class CustomS3Boto3Storage(S3Boto3Storage):
    file_overwrite = False


class StaticStorage(CustomS3Boto3Storage):
    location = 'static'


class MediaStorage(CustomS3Boto3Storage):
    location = 'media'
    

class ClientSVGStorage(CustomS3Boto3Storage):
    location = 'static/client'


def get_upload_path_prefix(type, *args):
    if type == 'business_registration':
        middle_path = ''
    elif type == 'product':
        middle_path = '/wholesaler{}'.format(*args)
    elif type == 'review':
        middle_path = '/shopper{}'.format(*args)
    else:
        return False

    return '{}{}/{}_'.format(type, middle_path, type)


def upload_images(type, images, *args):
    result = []
    temporary_images = []

    upload_path_prefix = get_upload_path_prefix(type, *args)
    if upload_path_prefix:
        storage = MediaStorage()
        for image in images:
            upload_path = upload_path_prefix + timezone.now().strftime(IMAGE_DATETIME_FORMAT) + os.path.splitext(image.name)[1].lower()
            storage.save(upload_path, image)
            temporary_images.append(TemporaryImage(image_url=upload_path))
            result.append(storage.url(upload_path))

    TemporaryImage.objects.bulk_create(temporary_images)

    return result
