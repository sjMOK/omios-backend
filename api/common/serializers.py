from rest_framework.exceptions import APIException
from rest_framework.serializers import Serializer, ModelSerializer, ImageField

from .validators import validate_file_size


MAXIMUM_NUMBER_OF_ITEMS = 100


def has_duplicate_element(array):
    if len(array) != len(set(array)):
        return True
    return False

def is_create_data(data):
    if bool(data) and 'id' not in data:
        return True
    return False

def is_update_data(data):
    if len(data.keys()) > 1 and 'id' in data:
        return True
    return False

def is_delete_data(data):
    if len(data.keys()) == 1 and 'id' in data:
        return True
    return False

def get_create_attrs(attrs):
    return [attr for attr in attrs if is_create_data(attr)]

def get_update_attrs(attrs):
    return [attr for attr in attrs if is_update_data(attr)]

def get_delete_attrs(attrs):
    return [attr for attr in attrs if is_delete_data(attr)]

def get_create_or_update_attrs(attrs):
    return [attr for attr in attrs if not is_delete_data(attr)]

def get_update_or_delete_attrs(attrs):
    return [attr for attr in attrs if not is_create_data(attr)]

def get_list_of_multi_values(attrs, *keys):
    return [tuple([attr[key] for key in keys if key in attr]) for attr in attrs]

def get_list_of_single_value(attrs, key):
    return [attr[key] for attr in attrs if key in attr]

def get_sum_of_single_value(attrs, key):
    return sum(get_list_of_single_value(attrs, key))

def add_data_in_each_element(list, key, value):
    for element in list:
        element[key] = value
    
    return list

def get_separated_data_by_create_update_delete(data_array):
        create_data = []
        delete_data = []
        update_data = []

        for data in data_array:
            if is_create_data(data):
                create_data.append(data)
            elif is_delete_data(data):
                delete_data.append(data)
            elif is_update_data:
                update_data.append(data)

        return (create_data, update_data, delete_data)


class SerializerMixin:
    ALL_FIELDS = '__all__'
    def __init__(self, *args, **kwargs):
        if 'allow_fields' in kwargs and 'exclude_fields' in kwargs:
            raise APIException('allow and exclude are incompatible.')

        allow_fields = kwargs.pop('allow_fields', None)
        exclude_fields = kwargs.pop('exclude_fields', None)

        super().__init__(*args, **kwargs)
        self.drop_fields(allow_fields, exclude_fields)

    def drop_fields(self, allow_fields=None, exclude_fields=None):
        if allow_fields is not None:
            self.remain_allow_fields(allow_fields)
        elif exclude_fields is not None:
            self.drop_exclude_fields(exclude_fields)
            

    def remain_allow_fields(self, allow_fields):
        if allow_fields == self.ALL_FIELDS:
            return
        elif not (isinstance(allow_fields, tuple) or isinstance(allow_fields, list)):
            raise APIException('allow_fields must be tuple or list instance.')

        allow_fields = set(allow_fields)
        existing_fields = set(self.fields)

        for field in allow_fields:
            if field not in existing_fields:
                raise APIException('allow_fields <{0}> not in serializer.fields.'.format(field))

        fields = set(self.fields) - set(allow_fields)
        for field in fields:
            self.fields.pop(field)

    def drop_exclude_fields(self, exclude_fields):
        if not (isinstance(exclude_fields, tuple) or isinstance(exclude_fields, list)):
            raise APIException('exclude_fields must be tuple or list instance.')
        
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


class ImageSerializer(Serializer):
    image = ImageField(max_length=200, validators=[validate_file_size])