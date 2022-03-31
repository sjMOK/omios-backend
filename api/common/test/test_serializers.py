from django.test import tag

from rest_framework.test import APISimpleTestCase
from rest_framework.serializers import Serializer, CharField, IntegerField
from rest_framework.exceptions import APIException

from ..serializers import (
    has_duplicate_element, is_create_data, is_update_data, is_delete_data,
    get_create_or_update_attrs, get_update_or_delete_attrs, get_list_of_single_item, SerializerMixin,
)
from .test_cases import FunctionTestCase


class HasDuplicateElementTestCase(FunctionTestCase):
    _function = has_duplicate_element

    def test_duplicated_array(self):
        array = [1, 2, 2, 3]

        self.assertTrue(self._call_function(array))

    def test_not_duplicated_array(self):
        array = [1, 2, 3]

        self.assertTrue(not self._call_function(array))


class IsCreateDeleteUpdateDataTestCase(APISimpleTestCase):
    def setUp(self):
        self.create_data = {
            'name': 'omios',
            'age': 1,
        }
        self.update_data = {
            'id': 100,
            'name': 'omios',
            'age': 1,
        }
        self.delete_data = {
            'id': 100,
        }
    
    def test_is_create_data(self):
        self.assertTrue(is_create_data(self.create_data))
        self.assertTrue(not is_create_data(self.update_data))
        self.assertTrue(not is_create_data(self.delete_data))

    def test_is_update_data(self):
        self.assertTrue(not is_update_data(self.create_data))
        self.assertTrue(is_update_data(self.update_data))
        self.assertTrue(not is_update_data(self.delete_data))

    def test_is_delete_data(self):
        self.assertTrue(not is_delete_data(self.create_data))
        self.assertTrue(not is_delete_data(self.update_data))
        self.assertTrue(is_delete_data(self.delete_data))


class GetAttrsTestCase(APISimpleTestCase):
    def setUp(self):
        self.create_attrs = [
            {'name': 'name1', 'age': 1},
            {'name': 'name2', 'age': 2},
        ]
        self.update_attrs = [
            {'id': 100, 'name': 'name100', 'age': 100},
            {'id': 101, 'name': 'name101', 'age': 101},
        ]
        self.delete_attrs = [
            {'id': 200},
            {'id': 201},
        ]
        self.attrs = self.create_attrs + self.update_attrs + self.delete_attrs
    
    def test_get_create_or_update_attrs(self):
        create_or_update_attrs = self.create_attrs + self.update_attrs

        self.assertListEqual(get_create_or_update_attrs(self.attrs), create_or_update_attrs)

    def test_get_update_or_delete_attrs(self):
        update_or_delete_attrs = self.update_attrs + self.delete_attrs

        self.assertListEqual(get_update_or_delete_attrs(self.attrs), update_or_delete_attrs)


class GetListOfSingleItemTestCase(FunctionTestCase):
    _function = get_list_of_single_item

    def test(self):
        attrs = [
            {'id': 1, 'name': 'name1'},
            {'id': 2, 'name': 'name2'},
            {'id': 3, 'name': 'name3'},
            {'id': 4, 'name': 'name4'},
        ]

        self.assertEqual(self._call_function('id', attrs), [1, 2, 3, 4])


class SerializerMixinTestCase(APISimpleTestCase):
    class DummySerializer(Serializer):
        name = CharField(max_length=20)
        age = IntegerField()
        mobile_number = CharField(max_length=20)
        address = CharField(max_length=50)


    class DummyTestSerializer(SerializerMixin, DummySerializer):
        pass


    def setUp(self):
        self.serializer_class = self.DummySerializer
        self.test_serializer_class = self.DummyTestSerializer
        self.allow_fields = self.exclude_fields = ('name', 'age')

    def test_default_create_serializer(self):
        serializer = self.serializer_class()
        test_serializer = self.test_serializer_class()

        self.assertSetEqual(set(test_serializer.fields), set(serializer.fields))

    def test_allow_fields(self):
        test_serializer = self.test_serializer_class(allow_fields=self.allow_fields)

        self.assertSetEqual(set(test_serializer.fields), set(self.allow_fields)) 

    def test_exclude_fields(self):
        serializer = self.serializer_class()
        test_serializer = self.test_serializer_class(exclude_fields=self.exclude_fields)

        self.assertSetEqual(set(test_serializer.fields), set(serializer.fields) - set(self.exclude_fields))

    def test_allow_all_fields(self):
        serializer = self.serializer_class()
        test_serializer = self.test_serializer_class(allow_fields='__all__')

        self.assertSetEqual(set(test_serializer.fields), set(serializer.fields))

    def test_allow_fields_and_excludes_fields_are_incompatible(self):
        self.assertRaisesRegex(
            APIException, 
            r'^allow and exclude are incompatible.$', 
            self.test_serializer_class,
            allow_fields=self.allow_fields, exclude_fields=self.exclude_fields
        )

    def test_allow_fields_must_be_tuple_or_list_by_string(self):
        allow_fields = ('id')

        self.assertRaisesRegex(
            APIException,
            r'^allow_fields must be tuple or list instance.$',
            self.test_serializer_class,
            allow_fields=allow_fields
        )

    def test_allow_fields_must_be_tuple_or_list_by_set(self):
        allow_fields = set(self.allow_fields)

        self.assertRaisesRegex(
            APIException,
            r'^allow_fields must be tuple or list instance.$',
            self.test_serializer_class,
            allow_fields=allow_fields
        )

    def test_exclude_fields_must_be_tuple_by_string(self):
        exclude_fields = ('id')

        self.assertRaisesRegex(
            APIException,
            r'^exclude_fields must be tuple or list instance.$',
            self.test_serializer_class,
            exclude_fields=exclude_fields
        )

    def test_exclude_fields_must_be_tuple(self):
        exclude_fields = set(self.exclude_fields)

        self.assertRaisesRegex(
            APIException,
            r'^exclude_fields must be tuple or list instance.$',
            self.test_serializer_class,
            exclude_fields=exclude_fields
        )

    def test_allow_wrong_fields(self):
        self.allow_fields += ('gender',)
        self.assertRaisesRegex(
            APIException,
            r'not in serializer.fields.$',
            self.test_serializer_class,
            allow_fields=self.allow_fields
        )

    def test_exclude_wrong_fields(self):
        self.exclude_fields += ('gender',)
        self.assertRaisesRegex(
            APIException,
            r'not in serializer.fields.$',
            self.test_serializer_class,
            exclude_fields=self.exclude_fields
        )
