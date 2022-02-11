import json
from datetime import datetime, timedelta
from django.http import QueryDict
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.exceptions import APIException

from .test import FunctionTestCase
from .utils import get_response_body, get_response, querydict_to_dict, gmt_to_kst


class GetResponseBodyTestCase(FunctionTestCase):
    _function = get_response_body

    def __set_expected_result(self, code, message='success', data=None):
        self.expected_result = {
            'code': code,
            'message': message,
        }

        if data is not None:
            self.expected_result['data'] = data

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
        result = self._call_function(code=201, data=['success', 'test'])

        self.assertDictEqual(result, self.expected_result)

    def test_failure(self):
        result = self._call_function(code=403, message=['failure', 'test'])

        self.assertDictEqual(result, self.expected_result)


class GetResponseTestCase(FunctionTestCase):
    _function = get_response

    def __set_expected_result(self, status=200, **kwargs):
        self.expected_result = get_response_body(code=status, **{key: value for key, value in kwargs.items() if key in ['message', 'data']})

    def _call_function(self, **kwargs):
        self.__set_expected_result(**kwargs)

        return super()._call_function(**kwargs)

    def test_default(self):
        result = self._call_function(data='default_test')

        self.assertIsInstance(result, Response)
        self.assertDictEqual(result.data, self.expected_result)
        self.assertEqual(result.status_code, result.data['code'])

    def test_django_response(self):
        result = self._call_function(type='django', status=201, data=['django', 'response', 'test'])

        self.assertIsInstance(result, JsonResponse)
        self.assertDictEqual(json.loads(result.content), self.expected_result)
        self.assertEqual(result.status_code, self.expected_result['code'])

    def test_drf_response(self):
        result = self._call_function(type='drf', status=400, message={'drf': 'drf', 'response': 'response', 'test': 'test'})

        self.assertIsInstance(result, Response)
        self.assertDictEqual(result.data, self.expected_result)
        self.assertEqual(result.status_code, result.data['code'])

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
