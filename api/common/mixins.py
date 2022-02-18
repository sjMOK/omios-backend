from rest_framework.exceptions import APIException

class SerializerMixin:
    def drop_fields(self, allow_fields=None, exclude_fields=None):
        if allow_fields is not None:
            if not isinstance(allow_fields, tuple):
                raise APIException('allow_fields must be tuple instance')

            allow_fields = set(allow_fields)
            existing_fields = set(self.fields)

            for field in allow_fields:
                if field not in existing_fields:
                    raise APIException('allow_fields <{0}> not in serializer.fields'.format(field))

            fields = set(self.fields) - set(allow_fields)
            for field in fields:
                self.fields.pop(field)

        elif exclude_fields is not None:
            if not isinstance(exclude_fields, tuple):
                raise APIException('exclude_fields must be tuple instance')

            exclude_fields = set(exclude_fields)
            existing_fields = set(self.fields)

            for field in exclude_fields:
                if field not in existing_fields:
                    raise APIException('exclude_fields <{0}> not in serializer.fields'.format(field))

                self.fields.pop(field)


    def __init__(self, *args, **kwargs):
        if 'allow_fields' in kwargs and 'exclude_fields' in kwargs:
            raise APIException('allow and exclude are incompatible.')

        allow_fields = kwargs.pop('allow_fields', None)
        exclude_fields = kwargs.pop('exclude_fields', None)

        super().__init__(*args, **kwargs)
        self.drop_fields(allow_fields, exclude_fields)
