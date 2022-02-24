import json
from datetime import datetime, timedelta

from django.http import QueryDict
from django.http import JsonResponse

from rest_framework.response import Response
from rest_framework.exceptions import APIException

from .test_cases import FunctionTestCase
from ..utils import get_response_body, get_response, querydict_to_dict, gmt_to_kst, datetime_to_iso, levenshtein


class GetResponseBodyTestCase(FunctionTestCase):
    _function = get_response_body

    def __set_expected_result(self, code, message='success', data=None):
        self.__expected_result = {
            'code': code,
            'message': message,
        }

        if data is not None:
            self.__expected_result['data'] = data

    def _call_function(self, **kwargs):
        self.__set_expected_result(**kwargs)

        return super()._call_function(**kwargs)

    def test_success_message_exception(self):
        self.assertRaisesRegex(APIException, r'^Success response must contain "success" message.$', self._call_function, code=201, message=['success', 'test'])

    def test_success_data_exception(self):
        self.assertRaisesRegex(APIException, r'^Success response must contain data.$', self._call_function, code=200)

    def test_failure_message_exception(self):
        self.assertRaisesRegex(APIException, r'^Failure response must not contain "success" message.$', self._call_function, code=400)

    def test_failure_data_exception(self):
        self.assertRaisesRegex(APIException, r'^Failure response must not contain data.$', self._call_function, code=500, message='failure test', data=['failure', 'test'])

    def test_success(self):
        self.assertDictEqual(self._call_function(code=201, data=['success', 'test']), self.__expected_result)

    def test_failure(self):
        self.assertDictEqual(self._call_function(code=403, message=['failure', 'test']), self.__expected_result)


class GetResponseTestCase(FunctionTestCase):
    _function = get_response

    def __set_expected_result(self, status=200, **kwargs):
        self.__expected_result = get_response_body(code=status, **{key: value for key, value in kwargs.items() if key in ['message', 'data']})

    def _call_function(self, **kwargs):
        self.__set_expected_result(**kwargs)

        return super()._call_function(**kwargs)

    def __test(self, expected_response_class, **kwargs):
        result = self._call_function(**kwargs)

        self.assertIsInstance(result, expected_response_class)
        self.assertDictEqual(result.data if expected_response_class == Response else json.loads(result.content), self.__expected_result)
        self.assertEqual(result.status_code, self.__expected_result['code'])

    def test_default(self):
        self.__test(Response, data='default_test')

    def test_django_response(self):
        self.__test(JsonResponse, type='django', status=201, data=['django', 'response', 'test'])

    def test_drf_response(self):
        self.__test(Response, type='drf', status=400, message={'drf': 'drf', 'response': 'response', 'test': 'test'})

    def test_error(self):
        self.assertRaises(TypeError, self._call_function, type='error_test', data='error_test')


class QuerydictToDictTestCase(FunctionTestCase):
    _function = querydict_to_dict

    def test(self):
        expected_result = {
            'a': ['1', '2', '3'],
            'b': '4',
            'c': ['5', '5'],
            'd': '6',
        }

        self.assertDictEqual(self._call_function(QueryDict('a=1&a=2&a=3&b=4&c=5&c=5&d=6')), expected_result)


class GmtToKstTestCase(FunctionTestCase):
    _function = gmt_to_kst

    def test(self):
        test_data = datetime.now()

        self.assertEqual(self._call_function(test_data), test_data + timedelta(hours=9))


class DateTimeToIsoTestCase(FunctionTestCase):
    _function = datetime_to_iso

    def test_datetime(self):
        test_data = datetime.now()

        self.assertEqual(self._call_function(test_data), test_data.isoformat())

    def test_string(self):
        self.assertIsNone(self._call_function('string'))

    def test_none(self):
        self.assertIsNone(self._call_function(None))


class LeveshteinTestCase(FunctionTestCase):
    _function = levenshtein

    def setUp(self):
        self.__basis_word = '원피스'

    def test_additional_string_in_front(self):
        self.assertEqual(self._call_function(self.__basis_word, '니트원피스'), 2)

    def test_additional_string_in_rear(self):
        self.assertEqual(self._call_function(self.__basis_word, '원피스 수영복'), 4)

    def test_similar_word(self):
        self.assertEqual(self._call_function(self.__basis_word, '원피피스'), 1)

    def test_completely_different_word(self):
        self.assertEqual(self._call_function(self.__basis_word, '체크가디건'), 5)
