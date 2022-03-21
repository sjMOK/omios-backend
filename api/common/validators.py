from rest_framework.validators import ValidationError


def validate_file_size(value):
    if value.size > 10485760:
        raise ValidationError("The maximum file size that can be uploaded is 10MB")

def validate_all_required_fields_included(attrs, fields):
    for key, value in fields.items():
        if getattr(value, 'required') and key not in attrs:
            raise ValidationError('{0} field is required.'.format(key))
