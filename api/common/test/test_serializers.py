from django.test import tag

from rest_framework.test import APISimpleTestCase
from rest_framework.serializers import Serializer, CharField, IntegerField
from rest_framework.exceptions import APIException

from ..serializers import SerializerMixin


class SerializerMixinTestCase(APISimpleTestCase):
    class DummySerializer(Serializer):
        name = CharField(max_length=20)
        age = IntegerField()
        phone = CharField(max_length=20)
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
