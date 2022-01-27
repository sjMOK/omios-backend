from django.http import QueryDict
from rest_framework.test import APISimpleTestCase

from .utils import get_result_message, querydict_to_dict


class GetResultMessageTestCase(APISimpleTestCase):
    def setUp(self):
        self.test_data = {
            'code': 200,
            'message': 'success',
            'data': None,
        }

    def call_function(self):
        return get_result_message(code=self.test_data['code'], message=self.test_data['message'], data=self.test_data['data'])

    def test_default(self):
        result = self.call_function()
        self.test_data.pop('data')
        self.assertDictEqual(result, self.test_data)
    
    def test_error(self):
        self.test_data['code'] = 500
        self.test_data['message'] = 'internal server error'
        result = self.call_function()
        self.test_data.pop('data')
        self.assertDictEqual(result, self.test_data)

    def test_success(self):
        self.test_data['code'] = 201
        self.test_data['data'] = ['get', 'result', 'message', 'test']
        self.assertDictEqual(self.call_function(), self.test_data)
        

class QuerydictToDictTestCase(APISimpleTestCase):
    def test(self):
        expected_result = {
            'a': ['1', '2', '3'],
            'b': '4',
            'c': ['5', '5'],
            'd': '6',
        }
        result = querydict_to_dict(QueryDict('a=1&a=2&a=3&b=4&c=5&c=5&d=6'))
        self.assertDictEqual(result, expected_result)
