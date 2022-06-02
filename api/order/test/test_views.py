from common.test.test_cases import ViewTestCase
from common.querysets import get_order_queryset
from product.models import Option
from product.test.factories import OptionFactory
from .factories import StatusHistoryFactory, create_orders_with_items, OrderItemFactory, ShippingAddressFactory, StatusFactory
from .test_serializers import (
    get_shipping_address_test_data, get_order_test_data, get_order_confirm_result,
    get_delivery_test_data, get_delivery_result,
)
from ..models import PAYMENT_COMPLETION_STATUS, DELIVERY_PREPARING_STATUS, DELIVERY_PROGRESSING_STATUS, OrderItem
from ..serializers import (
    ShippingAddressSerializer, OrderItemWriteSerializer, OrderSerializer, OrderWriteSerializer, 
    StatusHistorySerializer, OrderConfirmSerializer, DeliverySerializer,
)


class OrderViewSetTestCase(ViewTestCase):
    _url = '/orders'

    @classmethod
    def setUpTestData(cls):
        cls._set_shopper()
        cls.__shipping_address = ShippingAddressFactory()
        cls.__orders = create_orders_with_items(2, 3, False,
            {'shopper': cls._user, 'shipping_address': cls.__shipping_address}, {'status': StatusFactory(id=PAYMENT_COMPLETION_STATUS)})
        StatusFactory(id=DELIVERY_PREPARING_STATUS)
        StatusFactory(id=DELIVERY_PROGRESSING_STATUS)

    def setUp(self):
        self._set_authentication()

    def __get_queryset(self):
        return get_order_queryset().filter(shopper_id=self._user.id)

    def __set_detail_url(self):
        self.__order = self.__orders[0]
        self._url += f'/{self.__order.id}'

    def test_list(self):
        self._get()
        
        self._assert_success()
        self.assertListEqual(self._response_data, OrderSerializer(self.__get_queryset(), many=True).data)

    def test_create(self):
        options = Option.objects.select_related('product_color__product').all()
        self._test_data = get_order_test_data(self.__shipping_address, options, self._user)
        self._post(format='json')

        self._assert_success_and_serializer_class(OrderWriteSerializer)

    def test_retreive(self):
        self.__set_detail_url()
        order = self.__get_queryset().get(id=self.__order.id)
        self._get()
        
        self._assert_success()
        self.assertDictEqual(self._response_data, OrderSerializer(order).data)

    def test_update_shipping_address(self):
        self.__set_detail_url()
        self._url += '/shipping-address'
        self._test_data = get_shipping_address_test_data(ShippingAddressFactory.build())
        self._put()

        self._assert_success_and_serializer_class(ShippingAddressSerializer)
        self.assertEqual(self._response_data['id'], self.__order.id)

    def test_confirm(self):
        self._url += '/confirm'
        expected_result = get_order_confirm_result(OrderItem.objects.all(), 200)
        self._test_data = {'order_items': sum([data for data in list(expected_result.values())], [])}
        self._post()

        self._assert_success_and_serializer_class(OrderConfirmSerializer, False)
        self.assertDictEqual(self._response_data, expected_result)

    def test_delivery_request_data_size_validation(self):
        self._url += '/delivery'
        self._test_data = [''] * 51
        self._post(format='json')

        self._assert_failure(400, 'You can only request up to 50 at a time.')

    def test_delivery(self):
        self._url += '/delivery'
        order_items = OrderItem.objects.all()
        for order_item in order_items:
            order_item.status_id = DELIVERY_PREPARING_STATUS
        OrderItem.objects.bulk_update(order_items, ['status_id'])
        self._test_data = [get_delivery_test_data(order) for order in self.__orders]
        expected_result = get_delivery_result(self._test_data)
        self._post(format='json')

        self._assert_success_and_serializer_class(DeliverySerializer, False)
        self.assertDictEqual(self._response_data, expected_result)
        

class OrderItemViewSetTestCase(ViewTestCase):
    _url = '/orders/items'

    @classmethod
    def setUpTestData(cls):
        cls._set_shopper()
        cls.__order_item = OrderItem.objects.select_related('option__product_color').get(
            id=OrderItemFactory(order__shopper=cls._user, status=StatusFactory(id=PAYMENT_COMPLETION_STATUS)).id)
        cls._url += f'/{cls.__order_item.id}'

    def setUp(self):
        self._set_authentication()

    def test_partial_update_with_non_patchable_field(self):
        self._patch({'sale_price': 1000})

        self._assert_failure_for_non_patchable_field()

    def test_partial_update(self):
        self._patch({'option': OptionFactory(product_color=self.__order_item.option.product_color).id})

        self._assert_success_and_serializer_class(OrderItemWriteSerializer)


class ClaimViewSetTestCase(ViewTestCase):
    pass


class StatusHistoryTestCase(ViewTestCase):
    _url = '/orders/items'

    @classmethod
    def setUpTestData(cls):
        cls._set_shopper()
        cls.__order_item = OrderItemFactory(order__shopper=cls._user)
        cls._url += f'/{cls.__order_item.id}/status-histories'

    def setUp(self):
        self._set_authentication()

    def test_get(self):
        status_histories = StatusHistoryFactory.create_batch(3, order_item=self.__order_item)
        self._get()

        self._assert_success()
        self.assertListEqual(self._response_data, StatusHistorySerializer(status_histories, many=True).data)