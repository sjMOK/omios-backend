from rest_framework.exceptions import ValidationError
from rest_framework.serializers import Serializer, CharField, IntegerField

from .test_cases import FunctionTestCase
from ..validators import validate_all_required_fields_included


class ValidateRequireDataInPartialUpdateTestCase(FunctionTestCase):
    _function = validate_all_required_fields_included

    class DummySerializer(Serializer):
        age_not_required = IntegerField(required=False)
        name_required = CharField()

    def test(self):
        data = {}
        serializer = self.DummySerializer(data=data, partial=True)

        self.assertRaisesRegex(
            ValidationError,
            r'name_required field is required.',
            self._call_function,
            attrs=data, fields=serializer.fields
        )
