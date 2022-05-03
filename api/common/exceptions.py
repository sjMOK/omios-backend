from rest_framework.exceptions import APIException


class NotExcutableValidationError(APIException):
    default_detail = 'This serializer cannot validate.'