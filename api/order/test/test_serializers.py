from unittest.mock import patch
from random import randint
from copy import deepcopy
from dateutil.relativedelta import relativedelta

from django.utils import timezone
from django.forms import model_to_dict
from django.db.utils import DatabaseError
from django.db.models import Q

from freezegun import freeze_time

from common.test.test_cases import SerializerTestCase, ListSerializerTestCase, FREEZE_TIME
from common.querysets import get_order_item_queryset, get_order_queryset
from common.serializers import get_list_of_single_value, get_sum_of_single_value, add_data_in_each_element
from common.utils import DEFAULT_DATETIME_FORMAT, DATETIME_WITHOUT_MILISECONDS_FORMAT, datetime_to_iso
from user.models import Shopper
from user.test.factories import ShopperFactory
from product.serializers import OptionInOrderItemSerializer
from product.test.factories import ProductFactory, OptionFactory, create_options
from .factories import (
    create_orders_with_items, ShippingAddressFactory, OrderFactory, OrderItemFactory, 
    StatusFactory, StatusHistoryFactory, DeliveryFactory,
)
from ..models import (
    PAYMENT_COMPLETION_STATUS, DELIVERY_PREPARING_STATUS, DELIVERY_PROGRESSING_STATUS, NORMAL_STATUS,
    OrderItem, ShippingAddress, StatusHistory, Delivery
)
from ..serializers import (
    ShippingAddressSerializer, OrderItemSerializer, OrderItemWriteSerializer, OrderSerializer, OrderWriteSerializer, 
    RefundSerializer, CancellationInformationSerializer, StatusHistorySerializer, OrderConfirmSerializer, DeliverySerializer
)


def get_shipping_address_test_data(shipping_address):
    return {
        'receiver_name': shipping_address.receiver_name,
        'mobile_number': shipping_address.mobile_number,
        'phone_number': shipping_address.phone_number,
        'zip_code': shipping_address.zip_code,
        'base_address': shipping_address.base_address,
        'detail_address': shipping_address.detail_address,
        'shipping_message': shipping_address.shipping_message,
    }


def get_order_item_test_data(option, shopper):
    product = option.product_color.product
    count = randint(1, 5)

    test_data = {
        'count': count,
        'sale_price': product.sale_price * count,
        'base_discounted_price': product.base_discounted_price * count,
        'membership_discount_price': product.base_discounted_price * shopper.membership.discount_rate // 100 * count,
        'option': option.id,
    }
    test_data['payment_price'] = test_data['base_discounted_price'] - test_data['membership_discount_price']

    return test_data


def get_order_test_data(shipping_address, options, shopper):
    test_data = {
        'shipping_address': get_shipping_address_test_data(shipping_address),
        'items': [get_order_item_test_data(option, shopper) for option in options],
        'used_point': shopper.point // 2,
    }
    test_data['actual_payment_price'] = sum([item['payment_price'] for item in test_data['items']]) - test_data['used_point']
    test_data['earned_point'] = test_data['actual_payment_price'] // 100

    return test_data


def get_delivery_test_data(order, delivery=None):
    if isinstance(order, int):
        order_id = order
        order_items = [order-10, order-20]
    else:
        order_id = order.id
        order_items = [order_item.id for order_item in order.items.all()]
    
    if delivery is None:
        delivery = DeliveryFactory.build()
    
    return {
        'order': order_id,
        'order_items': order_items,
        'company': delivery.company,
        'invoice_number': delivery.invoice_number,
    }


def get_delivery_result(test_data):
    success = get_list_of_single_value(test_data, 'order')

    invalid_orders = [-2, -1]
    test_data += [get_delivery_test_data(order) for order in invalid_orders]

    other_delivery = DeliveryFactory()
    order_including_existed_invoice = test_data[0]
    order_including_existed_invoice['company'] = other_delivery.company
    order_including_existed_invoice['invoice_number'] = other_delivery.invoice_number
    success.remove(order_including_existed_invoice['order'])
    
    return {
        'success': success,
        'invalid_orders': invalid_orders,
        'existed_invoice': [order_including_existed_invoice['order']],
    }
    

def get_order_confirm_result(order_items, other_status_id):
    non_existent_order_item = [-2, -1]
    
    not_requestable_order_item = order_items[0]
    not_requestable_order_item.status_id = other_status_id
    not_requestable_order_item.save(update_fields=['status_id'])

    return {
        'success': list(order_items.exclude(status_id=other_status_id).values_list('id', flat=True)),
        'nonexistence': non_existent_order_item,
        'not_requestable_status': [not_requestable_order_item.id],
    }


class ShippingAddressSerializerTestCase(SerializerTestCase):
    _serializer_class = ShippingAddressSerializer

    @classmethod
    def setUpTestData(cls):
        cls.__shipping_address = ShippingAddressFactory()

    def setUp(self):
        self._test_data = get_shipping_address_test_data(self.__shipping_address)

    def __get_other_shipping_address(self, order=None):
        self._test_data['receiver_name'] += 'test'
        context = {}
        if order is not None:
            context['order'] = order

        return self._get_serializer(context=context).create(self._test_data)

    def test_model_instance_serialization(self):
        self._test_model_instance_serialization(self.__shipping_address, {
            'id': self.__shipping_address.id,
            **self._test_data,
        })

    def test_default_create(self):
        shipping_address = self.__get_other_shipping_address()

        self.assertTrue(self.__shipping_address.id != shipping_address)

    def test_create_with_existing_data(self):
        shipping_address = self._get_serializer().create(self._test_data)

        self.assertEqual(shipping_address, self.__shipping_address)

    def test_create_with_order(self):
        order = OrderFactory(shipping_address=self.__shipping_address)
        shipping_address = self.__get_other_shipping_address(order)

        self.assertEqual(order.shipping_address, shipping_address)


class OrderItemSerializerTestCase(SerializerTestCase):
    _serializer_class = OrderItemSerializer

    def test_model_instance_serialization(self):
        order_item = get_order_item_queryset().get(id=OrderItemFactory().id)

        self._test_model_instance_serialization(order_item, {
            'id': order_item.id,
            'option': OptionInOrderItemSerializer(order_item.option).data,
            'base_discount_price': order_item.base_discount_price,
            'earned_point': order_item.earned_point,
            'status': order_item.status.name,
            'count': order_item.count,
            'sale_price': order_item.sale_price,
            'membership_discount_price': order_item.membership_discount_price,
            'used_point': order_item.used_point,
            'payment_price': order_item.payment_price,
            'delivery': None,
        })

    def test_validation_error(self):
        self._test_not_excutable_validation()


class OrderItemListSerializerTestCase(ListSerializerTestCase):
    _child_serializer_class = OrderItemWriteSerializer

    @classmethod
    def setUpTestData(cls):
        cls.__shopper = ShopperFactory()
        cls.__order = OrderFactory(shopper=cls.__shopper)
        cls.__status = StatusFactory()
        cls.__options = create_options()
        cls._test_data = [get_order_item_test_data(option, cls.__shopper) for option in cls.__options]

    def _get_serializer(self, *args, **kwargs):
        return super()._get_serializer(context={'shopper': self.__shopper}, *args, **kwargs)

    def __create_order_items_by_factory(self):
        return [OrderItemFactory(order=self.__order, status=self.__status, option=option) for option in self.__options]

    def __assert_status_history_count(self, order_items):
        conditions = Q()
        for order_item in order_items:
            conditions |= Q(order_item=order_item, status_id=order_item.status_id)

        self.assertEqual(StatusHistory.objects.filter(conditions).count(), len(order_items))

    def test_validate_options(self):
        self._test_data.append(get_order_item_test_data(self.__options[0], self.__shopper))

        self._test_serializer_raise_validation_error('option is duplicated.')        

    def test_create_status_history(self):
        order_items = self.__create_order_items_by_factory()
        self._get_serializer()._OrderItemListSerializer__create_status_history(order_items)

        self.__assert_status_history_count(order_items)

    def test_create_after_validation(self):
        self.assertRaises(DatabaseError, self._save)

    def test_create(self):
        serializer = self._get_serializer_after_validation()
        add_data_in_each_element(serializer.validated_data, 'status', self.__status)
        add_data_in_each_element(serializer.validated_data, 'order', self.__order)
        order_items = serializer.save()

        self.assertListEqual([model_to_dict(order_item, exclude=['id']) for order_item in order_items], [{
            **data,
            'order': data['order'].id,
            'option': data['option'].id,
            'status': data['status'].id,
            'used_point': 0,
            'earned_point': 0,
            'delivery': None,
        } for data in serializer.validated_data])
        self.__assert_status_history_count(order_items)

    def test_update_status(self):
        status = StatusFactory()
        order_items = self._get_serializer().update_status(self.__create_order_items_by_factory(), status.id)

        for order_item in order_items:
            self.assertEqual(order_item.status_id, status.id)
        self.__assert_status_history_count(order_items)


class OrderItemWriteSerializerTestCase(SerializerTestCase):
    _serializer_class = OrderItemWriteSerializer

    @classmethod
    def setUpTestData(cls):
        cls.__shopper = ShopperFactory()
        cls.__option = OptionFactory()
        cls.__order_item = OrderItemFactory(order=OrderFactory(shopper=cls.__shopper), option=cls.__option, status=StatusFactory(id=PAYMENT_COMPLETION_STATUS))

        cls._test_data = get_order_item_test_data(cls.__option, cls.__shopper)

    def _get_serializer(self, *args, **kwargs):
        return super()._get_serializer(context={'shopper': self.__shopper}, *args, **kwargs)

    def __test_validate_price(self, update_key, expected_message):
        self._test_data[update_key] += 1
        self._test_serializer_raise_validation_error(expected_message)

    def test_validate_sale_price(self):
        self.__test_validate_price('sale_price', f'sale_price of option {self.__option.id} is different from the actual price.')

    def test_validate_base_discounted_price(self):
        self.__test_validate_price('base_discounted_price', f'base_discounted_price of option {self.__option.id} is different from the actual price.')

    def test_validate_membership_discount_price(self):
        self.__test_validate_price('membership_discount_price', f'membership_discount_price of option {self.__option.id} is different from the actual price.')

    def test_validate_payment_price(self):
        self.__test_validate_price('payment_price', f'payment_price of option {self.__option.id} is different from the actual price.')

    def test_validate_option_for_status(self):
        self.__order_item.status = StatusFactory(id=1000)

        self._test_serializer_raise_validation_error('This order is in a state where options cannot be changed.', self.__order_item)

    def test_validate_option(self):
        self._test_data = {'option': OptionFactory(product_color__product=ProductFactory(product=self.__option.product_color.product)).id}

        self._test_serializer_raise_validation_error('It cannot be changed to an option for another product.', self.__order_item)
        
    def test_validate_option_included_order(self):
        self._test_serializer_raise_validation_error('This item is already included in the order.', self.__order_item, {'option': self.__option.id})

    def test_validated_data_for_create(self):
        expected_data = deepcopy(self._test_data)
        expected_data['option'] = self.__option
        expected_data['base_discount_price'] = expected_data['sale_price'] - expected_data['base_discounted_price']
        del expected_data['base_discounted_price']

        self._test_validated_data(expected_data)

    def test_update(self):
        option = OptionFactory(product_color__product=self.__option.product_color.product)
        self._test_data = {'option': option.id}
        order_item = self._save(self.__order_item, partial=True)

        self.assertEqual(order_item.option, option)
        self.assertEqual(order_item, self.__order_item)


class OrderSerializerTestCase(SerializerTestCase):
    _serializer_class = OrderSerializer

    def test_model_instance_serialization(self):
        order = get_order_queryset().get(id=create_orders_with_items()[0].id)

        self._test_model_instance_serialization(order, {
            'id': order.id,
            'number': order.number,
            'shopper': order.shopper_id,
            'shipping_address': ShippingAddressSerializer(order.shipping_address).data,
            'items': OrderItemSerializer(order.items.all(), many=True).data,
            'created_at': datetime_to_iso(order.created_at),
        })

    def test_validation_error(self):
        self._test_not_excutable_validation()


class OrderWriteSerializerTestCase(SerializerTestCase):
    _serializer_class = OrderWriteSerializer

    @classmethod
    def setUpTestData(cls):
        shopper = ShopperFactory()
        cls.__shopper = Shopper.objects.select_related('membership').get(id=shopper.id)
        cls.__shipping_address = ShippingAddressFactory.build()
        cls.__options = create_options()
        cls.__status = StatusFactory()
        cls._test_data = get_order_test_data(cls.__shipping_address, cls.__options, cls.__shopper)

    def setUp(self):
        self.__total_payment_price = get_sum_of_single_value(self._test_data['items'], 'payment_price')

    def _get_serializer(self, *args, **kwargs):
        return super()._get_serializer(context={'shopper': self.__shopper}, *args, **kwargs)

    def __assert_point(self, items, key, point):
        extra_point = point - sum([int(item['payment_price'] * point / self.__total_payment_price) for item in items])

        self.assertTrue(items[0][key] - extra_point >= items[1][key]
            if items[0]['payment_price'] >= items[1]['payment_price'] else items[0][key] - extra_point < items[1][key]
        )
        self.assertEqual(get_sum_of_single_value(items, key), point)

    def __test_validate_price(self, update_key, expected_message):
        if update_key == 'used_point':
            self.__shopper.point = 0
        else:
            self._test_data[update_key] += 1

        self._test_serializer_raise_validation_error(expected_message)

    def test_validate_actual_payment_price(self):
        self.__test_validate_price('actual_payment_price', 'actual_payment_price is calculated incorrectly.')

    def test_validate_used_point(self):
        self.__test_validate_price('used_point', 'The shopper has less point than used_point.')

    def test_validate_earned_point(self):
        self.__test_validate_price('earned_point', 'earned_point is calculated incorrectly.')
    
    def test_distribute_point(self):
        key = 'test_key'
        point = 5000
        items = self._test_data['items']
        self._get_serializer()._OrderWriteSerializer__distribute_point(items, key, point, self.__total_payment_price)
        
        self.__assert_point(items, key, point)

    def test_apply_used_point_to_payment_price(self):
        items = self._test_data['items']
        serializer = self._get_serializer()
        serializer._OrderWriteSerializer__distribute_point(
            items, 'used_point', self._test_data['used_point'], self.__total_payment_price)
        serializer._OrderWriteSerializer__apply_used_point_to_payment_price(items)

        self.assertEqual(get_sum_of_single_value(items, 'payment_price'), self._test_data['actual_payment_price'])

    def test_set_items_including_point_informations(self):
        items = self._test_data['items']
        self._get_serializer()._OrderWriteSerializer__set_items_including_point_informations(
            items, self._test_data['used_point'], self._test_data['earned_point'], self.__total_payment_price
        )

        self.__assert_point(items, 'used_point', self._test_data['used_point'])
        self.__assert_point(items, 'earned_point', self._test_data['earned_point'])
        self.assertEqual(get_sum_of_single_value(items, 'payment_price'), self._test_data['actual_payment_price'])

    def test_validated_data_for_create(self):
        item_serializer = OrderItemWriteSerializer(many=True, data=self._test_data['items'], context={'shopper': self.__shopper})
        item_serializer.is_valid()
        self._get_serializer()._OrderWriteSerializer__set_items_including_point_informations(
            item_serializer.validated_data, self._test_data['used_point'], self._test_data['earned_point'], self.__total_payment_price
        )
        expected_data = deepcopy(self._test_data)
        expected_data['items'] = item_serializer.validated_data
        del expected_data['actual_payment_price'], expected_data['earned_point']
        
        self._test_validated_data(expected_data)

    def test_update_validation_error(self):
        self._test_not_excutable_validation(OrderFactory(shopper=self.__shopper))

    @freeze_time(FREEZE_TIME)
    def test_create(self):
        original_point = self.__shopper.point
        order = self._get_serializer_after_validation().save(status_id=self.__status.id)

        self.assertTrue(order.number.startswith(order.created_at.strftime(DEFAULT_DATETIME_FORMAT)))
        self.assertDictEqual(model_to_dict(order, exclude=['id']), {
            'number': order.number,
            'shopper': self.__shopper.id,
            'shipping_address': ShippingAddress.objects.get(**self._test_data['shipping_address']).id,
            'created_at': timezone.now(),
        })
        self.assertEqual(OrderItem.objects.filter(order_id=order.id).count(), len(self._test_data['items']))
        self.assertEqual(self.__shopper.point, original_point - self._test_data['used_point'])


class RefundSerializerTestCase(SerializerTestCase):
    _serializer_class = RefundSerializer


class CancellationInformationSerializerTestCase(SerializerTestCase):
    _serializer_class = CancellationInformationSerializer


class StatusHistorySerializerTestCase(SerializerTestCase):
    _serializer_class = StatusHistorySerializer

    @classmethod
    def setUpTestData(cls):
        cls.__order_items = create_orders_with_items()[0].items.all()

    def test_create(self):
        status_histories = [model_to_dict(status_history, exclude=['id']) for status_history in self._get_serializer().create(self.__order_items)]

        self.assertListEqual(status_histories, [{
            'order_item': order_item.id,
            'status': order_item.status_id,
        } for order_item in self.__order_items])

    def test_model_instance_serialization(self):
        status_history = StatusHistoryFactory(order_item=self.__order_items[0])

        self._test_model_instance_serialization(status_history, {
            'id': status_history.id,
            'status': status_history.status.name,
            'created_at': datetime_to_iso(status_history.created_at),
        })


class OrderConfirmSerializerTestCase(SerializerTestCase):
    _serializer_class = OrderConfirmSerializer

    @classmethod
    def setUpTestData(cls):
        cls.__original_status = StatusFactory(id=PAYMENT_COMPLETION_STATUS)
        create_orders_with_items(
            order_size=2, 
            only_product_color=True, 
            order_kwargs={'shopper': ShopperFactory()}, 
            item_kwargs={'status': cls.__original_status}
        )
    
        cls.__expected_result = get_order_confirm_result(OrderItem.objects.all(), StatusFactory(id=DELIVERY_PREPARING_STATUS).id)
        cls._test_data = {'order_items': sum([data for data in list(cls.__expected_result.values())], [])}

    def test_duplicated_order_items(self):
        self._test_data['order_items'].append(self._test_data['order_items'][0])

        self._test_serializer_raise_validation_error('order_item is duplicated.')

    def test_validate_order_items(self):
        serializer = self._get_serializer()
        order_items = serializer.validate_order_items(self._test_data['order_items'])

        self.assertQuerysetEqual(OrderItem.objects.filter(id__in=self.__expected_result['success']), order_items)
        self.assertListEqual(serializer._OrderConfirmSerializer__nonexistence, self.__expected_result['nonexistence'])
        self.assertListEqual(serializer._OrderConfirmSerializer__not_requestable_status, self.__expected_result['not_requestable_status'])
        
    @patch('order.serializers.OrderItemListSerializer._OrderItemListSerializer__create_status_history')
    def test_create(self, mock):
        serializer = self._get_serializer_after_validation()
        result = serializer.save()

        mock.assert_called_once()
        self.assertDictEqual(result, self.__expected_result)


class DeliveryListSerializerTestCase(ListSerializerTestCase):
    _child_serializer_class = DeliverySerializer

    @classmethod
    def setUpTestData(cls):
        cls.__status = StatusFactory(id=DELIVERY_PREPARING_STATUS)
        StatusFactory(id=DELIVERY_PROGRESSING_STATUS)
        cls.__orders = create_orders_with_items(order_size=3, only_product_color=True, order_kwargs={'shopper': ShopperFactory()}, item_kwargs={'status': cls.__status})
        cls._test_data = [get_delivery_test_data(order) for order in cls.__orders]
        cls.__expected_result = get_delivery_result(cls._test_data)

    def test_duplicated_orders(self):
        self._test_data[0]['order'] = self._test_data[1]['order']

        self._test_serializer_raise_validation_error('order is duplicated.')

    def test_duplicated_invoice(self):
        self._test_data[0]['company'] = self._test_data[1]['company']
        self._test_data[0]['invoice_number'] = self._test_data[1]['invoice_number']

        self._test_serializer_raise_validation_error('invoice_number is duplicated.')

    def test_set_failure_result(self):
        serializer = self._get_serializer_after_validation()

        self.assertListEqual(serializer._DeliveryListSerializer__invalid_orders, self.__expected_result['invalid_orders'])
        self.assertListEqual(serializer._DeliveryListSerializer__existed_invoice, self.__expected_result['existed_invoice'])

    @patch('order.serializers.OrderItemListSerializer.update_status')
    @freeze_time(FREEZE_TIME)
    def test_create(self, mock):
        result = self._get_serializer_after_validation().save()
        expected_order_items = sum([data['order_items'] for data in self._test_data if data['order'] in self.__expected_result['success']], [])
        success_order_items = OrderItem.objects.filter(
            order_id__in = self.__expected_result['success'],
            id__in = expected_order_items
        )
        deliveries = Delivery.objects.filter(id__in=success_order_items.values_list('delivery_id', flat=True)).all()
        
        self.assertEqual(len(set([delivery.flag for delivery in deliveries])), 1)
        self.assertTrue(deliveries[0].flag.startswith(timezone.now().strftime(DATETIME_WITHOUT_MILISECONDS_FORMAT)))
        self.assertListEqual([model_to_dict(delivery, exclude=['id']) for delivery in deliveries], [{
            'company': delivery['company'],
            'invoice_number': delivery['invoice_number'],
            'shipping_fee': 0,
            'flag': deliveries[0].flag,
        } for delivery in self._test_data if delivery['order'] in self.__expected_result['success']])
        self.assertEqual(OrderItem.objects.filter(delivery_id__in=[delivery.id for delivery in deliveries]).count(), len(expected_order_items))
        mock.assert_called_once()
        self.assertEqual(mock.call_args.args[1], 201)
        self.assertDictEqual(result, self.__expected_result)


class DeliverySerializerTestCase(SerializerTestCase):
    _serializer_class = DeliverySerializer

    @classmethod
    def setUpTestData(cls):
        cls.__status = StatusFactory(id=DELIVERY_PREPARING_STATUS)
        cls.__order = create_orders_with_items(only_product_color=True, item_kwargs={'status': cls.__status})[0]
        cls.__delivery = DeliveryFactory()
        cls._test_data = get_delivery_test_data(cls.__order)

    def __set_invalid_order_item(self, update_field):
        order_item = self.__order.items.all()[0]
        if update_field == 'status':
            order_item.status = StatusFactory(id=1000)
        elif update_field == 'delivery':
            order_item.delivery = self.__delivery
        order_item.save(update_fields=[update_field])

    def __test_invalid_order(self):
        serializer = self._get_serializer_after_validation()

        self.assertIsNone(serializer.validated_data['order_items'])

    def __set_duplicated_invoice_test_data(self):
        self._test_data['company'] = self.__delivery.company
        self._test_data['invoice_number'] = self.__delivery.invoice_number

    def test_duplicated_order_items(self):
        self._test_data['order_items'].append(self._test_data['order_items'][0])
        
        self._test_serializer_raise_validation_error(f'order_item of order {self.__order.id} is duplicated.')

    def test_other_order(self):
        self._test_data['order'] += 1

        self.__test_invalid_order()

    def test_other_status(self):
        self.__set_invalid_order_item('status')

        self.__test_invalid_order()

    def test_existed_delivery(self):
        self.__set_invalid_order_item('delivery')

        self.__test_invalid_order()

    def test_existed_invoice(self):
        self.__set_duplicated_invoice_test_data()
        serializer = self._get_serializer_after_validation()

        self.assertIsNone(serializer.validated_data['is_valid_invoice'])

    def test_existed_inovice_older_than_3months(self):
        self.__delivery.created_at = timezone.now() - relativedelta(months=3) - relativedelta(days=1)
        self.__delivery.save(update_fields=['created_at'])
        self.__set_duplicated_invoice_test_data()
        serializer = self._get_serializer_after_validation()

        self.assertTrue('is_valid_invoice' not in serializer.validated_data)
        
    def test_validated_data(self):
        validated_data = self._get_serializer_after_validation().validated_data
        validated_data['order_items'] = list(validated_data['order_items'])

        self.assertDictEqual(validated_data, {
            **self._test_data,
            'order_items': list(self.__order.items.all()),
        })
