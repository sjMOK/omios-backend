from rest_framework.exceptions import APIException
from rest_framework.serializers import Serializer, ModelSerializer

from django.core.exceptions import ObjectDoesNotExist


def convert_primary_key_related_field_to_serializer(serializer_class, instance, field, many=False):
        try:
            instance = getattr(instance, field)
        except ObjectDoesNotExist:
            return None

        return serializer_class(instance, many=many).data


class SerializerMixin:
    def __init__(self, *args, **kwargs):
        if 'allow_fields' in kwargs and 'exclude_fields' in kwargs:
            raise APIException('allow and exclude are incompatible.')

        allow_fields = kwargs.pop('allow_fields', None)
        exclude_fields = kwargs.pop('exclude_fields', None)

        super().__init__(*args, **kwargs)
        self.drop_fields(allow_fields, exclude_fields)

    def drop_fields(self, allow_fields=None, exclude_fields=None):
        if allow_fields is not None:
            if not (isinstance(allow_fields, tuple) or isinstance(allow_fields, list)):
                raise APIException('allow_fields must be tuple or list instance.')
            self.remain_allow_fields(allow_fields)
        elif exclude_fields is not None:
            if not (isinstance(exclude_fields, tuple) or isinstance(exclude_fields, list)):
                raise APIException('exclude_fields must be tuple or list instance.')
            self.exclude_fields(exclude_fields)
            

    def remain_allow_fields(self, allow_fields):
        allow_fields = set(allow_fields)
        existing_fields = set(self.fields)

        for field in allow_fields:
            if field not in existing_fields:
                raise APIException('allow_fields <{0}> not in serializer.fields.'.format(field))

        fields = set(self.fields) - set(allow_fields)
        for field in fields:
            self.fields.pop(field)

    def exclude_fields(self, exclude_fields):
        exclude_fields = set(exclude_fields)
        existing_fields = set(self.fields)

        for field in exclude_fields:
            if field not in existing_fields:
                raise APIException('exclude_fields <{0}> not in serializer.fields.'.format(field))

            self.fields.pop(field)


class DynamicFieldsSerializer(SerializerMixin, Serializer):
    pass


class DynamicFieldsModelSerializer(SerializerMixin, ModelSerializer):
    pass
