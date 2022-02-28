from rest_framework.validators import ValidationError


def validate_file_size(value):
    if value.size > 10485760:
        raise ValidationError("The maximum file size that can be uploaded is 10MB")