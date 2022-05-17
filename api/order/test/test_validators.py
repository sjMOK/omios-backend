from rest_framework.exceptions import ValidationError

from common.test.test_cases import FunctionTestCase
from ..validators import validate_order_items


class ValidateOrderItemsTestCase(FunctionTestCase):
    _function = validate_order_items

    class TemporaryOrderItemModel:
        def __init__(self, order_id=10, status_id=100):
            self.order_id = order_id
            self.status_id = status_id
    
    def setUp(self):
        self.__order_items = [self.TemporaryOrderItemModel() for _ in range(2)]

    def __test(self, error_message, order_id=None, status_id=None):
        self.assertRaisesRegex(
            ValidationError,
            r''+error_message,
            self._call_function,
            self.__order_items,
            order_id,
            status_id
        )

    def test_duplicated_order_items(self):
        self.__order_items.append(self.__order_items[0])

        self.__test('order_item is duplicated.')

    def test_variable_orders(self):
        self.__order_items.append(self.TemporaryOrderItemModel(order_id=20))

        self.__test('You can only make a request for one order and for order items that are all in the same status.')

    def test_variable_status(self):
        self.__order_items.append(self.TemporaryOrderItemModel(status_id=200))

        self.__test('You can only make a request for one order and for order items that are all in the same status.')
    
    def test_order_id(self):
        self.__test('The order requested and the order items are different.', order_id=20)

    def test_order_id(self):
        self.__test('The order_items cannot be requested.', status_id=[200])
