from django.utils import timezone
from storages.backends.s3boto3 import S3Boto3Storage
import os

class CustomS3Boto3Storage(S3Boto3Storage):
    file_overwrite = False


class StaticStorage(CustomS3Boto3Storage):
    location = 'static'


class MediaStorage(CustomS3Boto3Storage):
    location = 'media'
    

class ClientSVGStorage(CustomS3Boto3Storage):
    location = 'static/client'


def product_image_path(instance, filename):
    return 'product/wholesaler{0}/product{1}_{2}{3}'.format(
        instance.product.wholesaler.id,
        instance.product.id,
        timezone.now().strftime("%Y%m%d_%H%M%S%f"),
        os.path.splitext(filename)[1].lower(),
    )