import os

from storages.backends.s3boto3 import S3Boto3Storage

from django.utils import timezone


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


def get_upload_path_prefix(type, user_id):
    if type == 'product':
        return 'product/wholesaler{}/product_'.format(user_id)
    elif type == 'review':
        return 'review/shopper{}/review_'.format(user_id)
    else:
        return False


def upload_images(type, user_id, images):
    result = []

    upload_path_prefix = get_upload_path_prefix(type, user_id)
    if upload_path_prefix:
        storage = MediaStorage()
        for image in images:
            upload_path = upload_path_prefix + timezone.now().strftime("%Y%m%d_%H%M%S%f") + os.path.splitext(image.name)[1].lower()
            storage.save(upload_path, image)
            result.append(storage.url(upload_path))

    return result
