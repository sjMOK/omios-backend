from copy import deepcopy

from rest_framework.test import APISimpleTestCase
from rest_framework.serializers import Serializer, CharField, IntegerField
from rest_framework.exceptions import APIException 

from factory import RelatedFactoryList

from .test_cases import FunctionTestCase, ListSerializerTestCase, SerializerTestCase
from .factories import SettingGroupFactory, SettingItemFactory
from ..models import SettingGroup
from ..serializers import (
    SerializerMixin, SettingItemSerializer, SettingGroupSerializer,
    has_duplicate_element, is_create_data, is_update_data, is_delete_data, get_create_attrs,
    get_update_attrs, get_delete_attrs, get_create_or_update_attrs, get_update_or_delete_attrs, 
    get_list_of_single_value, get_sum_of_single_value, add_data_in_each_element,
)


list_test_data = [
    {'id': 1, 'name': 'name1'},
    {'id': 2, 'name': 'name2'},
    {'id': 3, 'name': 'name3'},
    {'id': 4, 'name': 'name4'},
]


def get_setting_groups_test_data(**kwargs):
    default_setting_group = SettingGroupFactory(
        main_key='default', items=RelatedFactoryList(SettingItemFactory, 'group'), **kwargs,
    )
    same_main_key_setting_groups = SettingGroupFactory.create_batch(
        2, main_key='same_main_key', items=RelatedFactoryList(SettingItemFactory, 'group'), **kwargs,
    )
    using_sub_key_setting_groups = []
    for i in range(2):
        using_sub_key_setting_groups.append(SettingGroupFactory.create(
            main_key='using_sub_key', sub_key=f'sub_key{i}', items=RelatedFactoryList(SettingItemFactory, 'group'), **kwargs
        ))

    return default_setting_group, same_main_key_setting_groups, using_sub_key_setting_groups


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
        self.__create_data = {
            'name': 'omios',
            'age': 1,
        }
        self.__update_data = {
            'id': 100,
            'name': 'omios',
            'age': 1,
        }
        self.__delete_data = {
            'id': 100,
        }
    
    def test_is_create_data(self):
        self.assertTrue(is_create_data(self.__create_data))
        self.assertTrue(not is_create_data(self.__update_data))
        self.assertTrue(not is_create_data(self.__delete_data))

    def test_is_update_data(self):
        self.assertTrue(not is_update_data(self.__create_data))
        self.assertTrue(is_update_data(self.__update_data))
        self.assertTrue(not is_update_data(self.__delete_data))

    def test_is_delete_data(self):
        self.assertTrue(not is_delete_data(self.__create_data))
        self.assertTrue(not is_delete_data(self.__update_data))
        self.assertTrue(is_delete_data(self.__delete_data))


class GetAttrsTestCase(APISimpleTestCase):
    def setUp(self):
        self.__create_attrs = [
            {'name': 'name1', 'age': 1},
            {'name': 'name2', 'age': 2},
        ]
        self.__update_attrs = [
            {'id': 100, 'name': 'name100', 'age': 100},
            {'id': 101, 'name': 'name101', 'age': 101},
        ]
        self.__delete_attrs = [
            {'id': 200},
            {'id': 201},
        ]
        self.__attrs = self.__create_attrs + self.__update_attrs + self.__delete_attrs
    
    def test_get_create_attrs(self):
        self.assertListEqual(get_create_attrs(self.__attrs), self.__create_attrs)

    def test_get_update_attrs(self):
        self.assertListEqual(get_update_attrs(self.__attrs), self.__update_attrs)

    def test_get_delete_attrs(self):
        self.assertListEqual(get_delete_attrs(self.__attrs), self.__delete_attrs)

    def test_get_create_or_update_attrs(self):
        create_or_update_attrs = self.__create_attrs + self.__update_attrs

        self.assertListEqual(get_create_or_update_attrs(self.__attrs), create_or_update_attrs)

    def test_get_update_or_delete_attrs(self):
        update_or_delete_attrs = self.__update_attrs + self.__delete_attrs

        self.assertListEqual(get_update_or_delete_attrs(self.__attrs), update_or_delete_attrs)


class GetListOfSingleValueTestCase(FunctionTestCase):
    _function = get_list_of_single_value

    def test(self):
        self.assertListEqual(self._call_function(list_test_data, 'id'), [data['id'] for data in list_test_data])


class GetSumOfSingleValue(FunctionTestCase):
    _function = get_sum_of_single_value

    def test(self):
        self.assertEqual(self._call_function(list_test_data, 'id'), sum([data['id'] for data in list_test_data]))


class AddDataInEachElement(FunctionTestCase):
    _function = add_data_in_each_element

    def test(self):
        expected_result = deepcopy(list_test_data)
        key = 'test_key'
        value = 'test_value'
        for element in expected_result:
            element[key] = value

        self.assertListEqual(self._call_function(list_test_data, key, value), expected_result)


class SerializerMixinTestCase(APISimpleTestCase):
    class DummySerializer(Serializer):
        name = CharField(max_length=20)
        age = IntegerField()
        mobile_number = CharField(max_length=20)
        address = CharField(max_length=50)


    class DummyTestSerializer(SerializerMixin, DummySerializer):
        pass


    def setUp(self):
        self.__serializer_class = self.DummySerializer
        self.__test_serializer_class = self.DummyTestSerializer
        self.__allow_fields = self.__exclude_fields = ('name', 'age')

    def test_default_create_serializer(self):
        serializer = self.__serializer_class()
        test_serializer = self.__test_serializer_class()

        self.assertSetEqual(set(test_serializer.fields), set(serializer.fields))

    def test_allow_fields(self):
        test_serializer = self.__test_serializer_class(allow_fields=self.__allow_fields)

        self.assertSetEqual(set(test_serializer.fields), set(self.__allow_fields)) 

    def test_exclude_fields(self):
        serializer = self.__serializer_class()
        test_serializer = self.__test_serializer_class(exclude_fields=self.__exclude_fields)

        self.assertSetEqual(set(test_serializer.fields), set(serializer.fields) - set(self.__exclude_fields))

    def test_allow_all_fields(self):
        serializer = self.__serializer_class()
        test_serializer = self.__test_serializer_class(allow_fields='__all__')

        self.assertSetEqual(set(test_serializer.fields), set(serializer.fields))

    def test_allow_fields_and_excludes_fields_are_incompatible(self):
        self.assertRaisesRegex(
            APIException, 
            r'^allow and exclude are incompatible.$', 
            self.__test_serializer_class,
            allow_fields=self.__allow_fields, exclude_fields=self.__exclude_fields
        )

    def test_allow_fields_must_be_tuple_or_list_by_string(self):
        allow_fields = ('id')

        self.assertRaisesRegex(
            APIException,
            r'^allow_fields must be tuple or list instance.$',
            self.__test_serializer_class,
            allow_fields=allow_fields
        )

    def test_allow_fields_must_be_tuple_or_list_by_set(self):
        allow_fields = set(self.__allow_fields)

        self.assertRaisesRegex(
            APIException,
            r'^allow_fields must be tuple or list instance.$',
            self.__test_serializer_class,
            allow_fields=allow_fields
        )

    def test_exclude_fields_must_be_tuple_by_string(self):
        exclude_fields = ('id')

        self.assertRaisesRegex(
            APIException,
            r'^exclude_fields must be tuple or list instance.$',
            self.__test_serializer_class,
            exclude_fields=exclude_fields
        )

    def test_exclude_fields_must_be_tuple(self):
        exclude_fields = set(self.__exclude_fields)

        self.assertRaisesRegex(
            APIException,
            r'^exclude_fields must be tuple or list instance.$',
            self.__test_serializer_class,
            exclude_fields=exclude_fields
        )

    def test_allow_wrong_fields(self):
        self.__allow_fields += ('gender',)
        self.assertRaisesRegex(
            APIException,
            r'not in serializer.fields.$',
            self.__test_serializer_class,
            allow_fields=self.__allow_fields
        )

    def test_exclude_wrong_fields(self):
        self.__exclude_fields += ('gender',)
        self.assertRaisesRegex(
            APIException,
            r'not in serializer.fields.$',
            self.__test_serializer_class,
            exclude_fields=self.__exclude_fields
        )


class SettingItemSerializerTestCase(SerializerTestCase):
    _serializer_class = SettingItemSerializer

    def test_model_instance_serialization(self):
        setting_item = SettingItemFactory()

        self._test_model_instance_serialization(setting_item, {
            'id': setting_item.id,
            'name': setting_item.name,
        })


class SettingGroupListSerializerTestCase(ListSerializerTestCase):
    _child_serializer_class = SettingGroupSerializer

    def test_model_instance_serialization(self):
        default_setting_group, same_main_key_setting_groups, using_sub_key_setting_groups = get_setting_groups_test_data()

        self._test_model_instance_serialization(SettingGroup.objects.prefetch_related('items').all(), {
            **{default_setting_group.main_key: SettingGroupSerializer(default_setting_group).data},
            **{same_main_key_setting_groups[0].main_key: [
                SettingGroupSerializer(setting_group).data 
            for setting_group in same_main_key_setting_groups]},
            **{using_sub_key_setting_groups[0].main_key: {
                setting_group.sub_key: SettingGroupSerializer(setting_group).data
            for setting_group in using_sub_key_setting_groups}}
        })


class SettingGroupSerializerTestCase(SerializerTestCase):
    _serializer_class = SettingGroupSerializer

    def test_model_instance_serialization(self):
        setting_group = SettingGroupFactory(items=RelatedFactoryList(SettingItemFactory, 'group'))

        self._test_model_instance_serialization(setting_group, {
            'name': setting_group.name,
            'items': SettingItemSerializer(setting_group.items, many=True).data,
        })
        