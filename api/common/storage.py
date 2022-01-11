from storages.backends.s3boto3 import S3Boto3Storage

class CustomS3Boto3Storage(S3Boto3Storage):
    file_overwrite = False


class StaticStorage(CustomS3Boto3Storage):
    location = 'static'


class MediaStorage(CustomS3Boto3Storage):
    location = 'media'
    

class ClientSVGStorage(CustomS3Boto3Storage):
    location = 'static/client'
