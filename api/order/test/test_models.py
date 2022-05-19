from django.forms import model_to_dict
from django.utils import timezone

from freezegun import freeze_time

from common.test.test_cases import ModelTestCase, FREEZE_TIME
from common.utils import DEFAULT_DATETIME_FORMAT
from user.test.factories import ShopperFactory
from product.test.factories import OptionFactory
from .factories import OrderFactory, OrderItemFactory, RefundFactory, StatusFactory, ShippingAddressFactory
from ..models import (
    Order, OrderItem, Status, StatusHistory, ShippingAddress,
    CancellationInformation, ExchangeInformation, ReturnInformation, Refund, Delivery
)


@freeze_time(FREEZE_TIME)
class OrderTestCase(ModelTestCase):
    _model_class = Order

    @classmethod
    def setUpTestData(cls):
        cls._test_data = {
            'shopper': ShopperFactory(),
            'shipping_address': ShippingAddressFactory(),
        }
        cls._order = cls._get_default_model_after_creation()

    def test_create(self):
        order = model_to_dict(self._order, exclude=['id'])

        self.assertTrue(order['number'].startswith(order['created_at'].strftime(DEFAULT_DATETIME_FORMAT)))
        self.assertDictEqual(order, {
            'shopper': self._test_data['shopper'].id,
            'shipping_address': self._test_data['shipping_address'].id,
            'number': order['number'],
            'created_at': timezone.now(),
        })

    def test_set_default_number(self):
        self._test_data['number'] = self._order.number
        new_order = self._get_model_after_creation()
        
        self.assertTrue(self._order.number != new_order.number)
        self.assertTrue(new_order.number.startswith(new_order.created_at.strftime(DEFAULT_DATETIME_FORMAT)))


class OrderItemTestCase(ModelTestCase):
    _model_class = OrderItem

    def setUp(self):
        option = OptionFactory()
        self._test_data = {
            'order': OrderFactory(),
            'option': option,
            'status': StatusFactory(),
            'sale_price': 10000,
            'membership_discount_price': '100',
            'payment_price': 9900,
            'earned_point': '99',
        }

    def test_create(self):
        order_item = model_to_dict(self._get_model_after_creation(), exclude=['id'])

        self.assertDictEqual(order_item, {
            **self._test_data,
            'order': self._test_data['order'].id,
            'option': self._test_data['option'].id,
            'status': self._test_data['status'].id,
            'base_discount_price': 0,
            'count': 1,
            'used_point': 0,
            'delivery': None,
        })


class StatusTestCase(ModelTestCase):
    _model_class = Status

    def setUp(self):
        self._test_data = {
            'id': 1000,
            'name' : 'status_test',
        }

    def test_create(self):
        status = model_to_dict(self._get_model_after_creation())

        self.assertDictEqual(status, self._test_data)


class StatusHistoryTestCase(ModelTestCase):
    _model_class = StatusHistory

    def setUp(self):
        order_item = OrderItemFactory()
        self._test_data = {
            'order_item': order_item,
            'status': order_item.status,
        }

    def test_create(self):
        status_history = model_to_dict(self._get_model_after_creation(), exclude=['id'])

        self.assertDictEqual(status_history, {
            'order_item': self._test_data['order_item'].id,
            'status': self._test_data['status'].id,
        })


class ShippingAddressTestCase(ModelTestCase):
    _model_class = ShippingAddress

    def setUp(self):
        self._test_data = {
            'receiver_name': '수령자명',
            'mobile_number': '01012345678',
            'phone_number': '0212345678',
            'zip_code': '12345',
            'base_address': '기본주소',
            'detail_address': '상세주소',
            'shipping_message': '배송메시지',
        }

    def test_create(self):
        shipping_address = model_to_dict(self._get_model_after_creation(), exclude=['id'])

        self.assertDictEqual(shipping_address, self._test_data)


class CancellationInformationTestCase(ModelTestCase):
    _model_class = CancellationInformation

    def setUp(self):
        self._test_data = {
            'order_item': OrderItemFactory(),
            'refund': RefundFactory(),
        }

    def test_create(self):
        cancellation_information = model_to_dict(self._get_model_after_creation())

        self.assertDictEqual(cancellation_information, {
            'order_item': self._test_data['order_item'].id,
            'refund': self._test_data['refund'].id,
        })


class ExchangeInformationTestCase(ModelTestCase):
    _model_class = ExchangeInformation


class ReturnInformationTestCase(ModelTestCase):
    _model_class = ReturnInformation


class RefundTestCase(ModelTestCase):
    _model_class = Refund

    def setUp(self):
        self._test_data = {
            'price': 10000,
        }

    def test_create(self):
        refund = model_to_dict(self._get_model_after_creation(), exclude=['id'])

        self.assertDictEqual(refund, {
            **self._test_data,
            'completed_at': None,
        })


class DeliveryTestCase(ModelTestCase):
    _model_class = Delivery

    def setUp(self):
        self._test_data = {
            'company': 'delivery_company',
            'invoice_number': '1234-1234-1234',
            'flag': 'flag_test',
        }

    def test_create(self):
        delivery = model_to_dict(self._get_model_after_creation(), exclude=['id'])

        self.assertDictEqual(delivery, {
            **self._test_data,
            'shipping_fee': 0,
            'flag': self._test_data['flag'],
        })
