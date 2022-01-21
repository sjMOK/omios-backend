from multiprocessing import Value
from django.core.exceptions import ValidationError


def validate_file_size(value):
    if value.size > 10485760:
        raise ValidationError("The maximum file size that can be uploaded is 10MB")
    else:
        return value