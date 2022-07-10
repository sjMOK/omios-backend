from unittest.mock import patch
from random import randint
from copy import deepcopy
from dateutil.relativedelta import relativedelta

from django.utils import timezone
from django.forms import model_to_dict
from django.db.utils import DatabaseError
from django.db.models import Q
from django.db.models.query import Prefetch

from freezegun import freeze_time

from common.test.test_cases import SerializerTestCase, ListSerializerTestCase, FREEZE_TIME
from common.serializers import get_list_of_single_value, get_sum_of_single_value, add_data_in_each_element
from common.utils import DEFAULT_DATETIME_FORMAT, DATETIME_WITHOUT_MILISECONDS_FORMAT, datetime_to_iso
from user.models import Shopper
from user.test.factories import ShopperFactory, ShopperCouponFactory
from product.models import ProductImage
from product.serializers import OptionInOrderItemSerializer
from product.test.factories import ProductFactory, OptionFactory, create_options
from coupon.models import ALL_PRODUCT_COUPON_CLASSIFICATIONS, SOME_PRODUCT_COUPON_CLASSIFICATION, SUB_CATEGORY_COUPON_CLASSIFICATION
from coupon.test.factories import CouponClassificationFactory, CouponFactory
from .factories import (
    create_orders_with_items, ShippingAddressFactory, OrderFactory, OrderItemFactory, 
    StatusFactory, StatusHistoryFactory, DeliveryFactory,
)
from ..models import (
    PAYMENT_COMPLETION_STATUS, DELIVERY_PREPARING_STATUS, DELIVERY_PROGRESSING_STATUS, NORMAL_STATUS,
    Order, OrderItem, ShippingAddress, StatusHistory, Delivery
)
from ..serializers import (
    ShippingAddressSerializer, OrderItemSerializer, OrderItemWriteSerializer, OrderSerializer, OrderWriteSerializer, 
    OrderItemStatisticsSerializer, RefundSerializer, CancellationInformationSerializer, StatusHistorySerializer, 
    OrderConfirmSerializer, DeliverySerializer,
)


def get_order_item_queryset():
    images = ProductImage.objects.filter(sequence=1)
    return OrderItem.objects.select_related('option__product_color__product', 'status'). \
        prefetch_related(Prefetch('option__product_color__product__images', images))


def get_order_queryset(queryset=Order.objects, item_queryset=get_order_item_queryset()):
    return queryset.select_related('shipping_address'). \
        prefetch_related(Prefetch('items', item_queryset))


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


def get_order_item_test_data(option, shopper, shopper_coupon=None):
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

    if shopper_coupon is not None:
        test_data['shopper_coupon'] = shopper_coupon.id
        test_data['coupon_discount_price'] = OrderItemWriteSerializer()._OrderItemWriteSerializer__get_actual_coupon_discount_price(
            shopper_coupon.coupon, product, test_data['payment_price'] // count
        )
        test_data['payment_price'] -= test_data['coupon_discount_price']

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
        cls.__order = create_orders_with_items(
            item_size = 1,
            order_kwargs = {'shipping_address': cls.__shipping_address},
            item_kwargs = {'status': StatusFactory(id=1000), 'shopper_coupon': None},
        )[0]

    def setUp(self):
        self._test_data = get_shipping_address_test_data(self.__shipping_address)

    def __get_context(self, order=True):
        if order:
            return {'order': self.__order}
        else:
            return {}

    def __get_other_shipping_address(self, order=False):
        self._test_data['receiver_name'] += 'test'

        return self._get_serializer(context=self.__get_context(order)).create(self._test_data)

    def test_validate_status(self):
        self._test_serializer_raise_validation_error('The shipping address for this order cannot be changed.', context=self.__get_context())

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
        shipping_address = self.__get_other_shipping_address(True)

        self.assertTrue(self.__order.shipping_address != self.__shipping_address)
        self.assertEqual(self.__order.shipping_address, shipping_address)


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
            'shopper_coupon': str(order_item.shopper_coupon),
            'coupon_discount_price': order_item.coupon_discount_price,
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
        cls.__coupons = ShopperCouponFactory.create_batch(
            2,
            shopper=cls.__shopper, 
            is_used=False, 
            coupon__classification=CouponClassificationFactory(id=ALL_PRODUCT_COUPON_CLASSIFICATIONS[0]),
        )
        cls._test_data = [get_order_item_test_data(option, cls.__shopper, coupon) for option, coupon in zip(cls.__options, cls.__coupons)]

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

    def test_validate_shopper_coupons(self):
        self._test_data = [get_order_item_test_data(option, self.__shopper, self.__coupons[0]) for option in self.__options]

        self._test_serializer_raise_validation_error('shopper_coupon is duplicated.')

    def test_create_status_history(self):
        order_items = self.__create_order_items_by_factory()
        self._get_serializer()._OrderItemListSerializer__create_status_history(order_items)

        self.__assert_status_history_count(order_items)

    def test_create_after_validation(self):
        self.assertRaises(DatabaseError, self._save)

    @patch('user.serializers.ShopperCouponSerializer.update_is_used')
    def test_create(self, mock):
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
            'shopper_coupon': data['shopper_coupon'].id,
            'coupon_discount_price': data['coupon_discount_price'],
        } for data in serializer.validated_data])
        mock.assert_called_once()
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
        cls.__product = cls.__option.product_color.product
        
        cls.__coupon = ShopperCouponFactory(
            shopper=cls.__shopper, 
            is_used=False, 
            coupon=CouponFactory(classification=CouponClassificationFactory(id=ALL_PRODUCT_COUPON_CLASSIFICATIONS[0]))
        )
        CouponClassificationFactory(id=SOME_PRODUCT_COUPON_CLASSIFICATION)
        CouponClassificationFactory(id=SUB_CATEGORY_COUPON_CLASSIFICATION)

        cls.__order_item = OrderItemFactory(
            order=OrderFactory(shopper=cls.__shopper), 
            option=cls.__option, 
            status=StatusFactory(id=PAYMENT_COMPLETION_STATUS), 
            shopper_coupon = None,
        )

        cls._test_data = get_order_item_test_data(cls.__option, cls.__shopper, cls.__coupon)

    def _get_serializer(self, *args, **kwargs):
        return super()._get_serializer(context={'shopper': self.__shopper}, *args, **kwargs)

    def __set_up_get_actual_coupon_discount_price(self, target):
        if target in ['discount_rate', 'coupont_maximum_discount_price']:
            self.__coupon = CouponFactory.build(maximum_discount_price=None)
        elif target in ['discount_price', 'maximum_discount_price']:
            self.__coupon = CouponFactory.build(discount_price=True)

        self.__product = ProductFactory.build()
        self.__maximum_discount_price = self.__product.base_discounted_price + 1

    def __set_classification(self, classification_id):
        self.__coupon.coupon.classification_id = classification_id
        self.__coupon.coupon.save(update_fields=['classification'])

    def __test_get_actual_coupon_discount_price(self, expected_result, maximum_discount_price=None):
        result = self._get_serializer()._OrderItemWriteSerializer__get_actual_coupon_discount_price(
            self.__coupon, self.__product, maximum_discount_price or self.__maximum_discount_price
        )
        
        self.assertEqual(result, expected_result)

    def __test_validate_shopper_coupon(self, update_key, expected_message):
        self.__coupon.save(update_fields=[update_key])
        self._test_serializer_raise_validation_error(expected_message)

    def __test_validate_price(self, update_key, expected_message):
        self._test_data[update_key] += 1
        self._test_serializer_raise_validation_error(expected_message)

    def test_get_actual_coupon_discount_price_about_discount_rate(self):
        self.__set_up_get_actual_coupon_discount_price('discount_rate')

        self.__test_get_actual_coupon_discount_price(self.__product.base_discounted_price * self.__coupon.discount_rate // 100)

    def test_get_actual_coupon_discount_price_about_coupont_maximum_discount_price(self):
        self.__set_up_get_actual_coupon_discount_price('coupont_maximum_discount_price')
        self.__coupon.maximum_discount_price = self.__product.base_discounted_price * self.__coupon.discount_rate // 100 - 1

        self.__test_get_actual_coupon_discount_price(self.__coupon.maximum_discount_price)

    def test_get_actual_coupon_discount_price_about_discount_price(self):
        self.__set_up_get_actual_coupon_discount_price('discount_price')

        self.__test_get_actual_coupon_discount_price(self.__coupon.discount_price)

    def test_get_actual_coupon_discount_price_about_maximum_discount_price(self):        
        self.__set_up_get_actual_coupon_discount_price('maximum_discount_price')
        maximum_discount_price = self.__coupon.discount_price - 1

        self.__test_get_actual_coupon_discount_price(maximum_discount_price, maximum_discount_price)

    def test_validate_sale_price(self):        
        self.__test_validate_price('sale_price', f'sale_price of option {self.__option.id} is different from the actual price.')

    def test_validate_base_discounted_price(self):        
        self.__test_validate_price('base_discounted_price', f'base_discounted_price of option {self.__option.id} is different from the actual price.')

    def test_validate_membership_discount_price(self):        
        self.__test_validate_price('membership_discount_price', f'membership_discount_price of option {self.__option.id} is different from the actual price.')

    def test_validate_payment_price(self):        
        self.__test_validate_price('payment_price', f'payment_price of option {self.__option.id} is different from the actual price.')

    def test_validate_shopper_coupon_about_is_used(self):        
        self.__coupon.is_used = True
        
        self.__test_validate_shopper_coupon('is_used', f'shopper_coupon {self.__coupon.id} is expired or have already been used.')

    def test_validate_shopper_coupon_about_end_date(self):        
        self.__coupon.end_date = timezone.now() - relativedelta(days=2)

        self.__test_validate_shopper_coupon('end_date', f'shopper_coupon {self.__coupon.id} is expired or have already been used.')

    def test_validate_shopper_coupon_about_shopper(self):        
        self.__coupon.shopper = ShopperFactory(membership=self.__shopper.membership)

        self.__test_validate_shopper_coupon('shopper', f'shopper_coupon {self.__coupon.id} belongs to someone else.')

    def test_validate_coupon_without_shopper_coupon(self):        
        del self._test_data['shopper_coupon']

        self._test_serializer_raise_validation_error(f'shopper_coupon and coupon_discount_price of option {self.__option.id} must be requested together.')

    def test_validate_coupon_without_coupon_discount_price(self):        
        del self._test_data['coupon_discount_price']

        self._test_serializer_raise_validation_error(f'shopper_coupon and coupon_discount_price of option {self.__option.id} must be requested together.')

    def test_validate_coupon_about_some_product_coupon_classification(self):        
        self.__set_classification(SOME_PRODUCT_COUPON_CLASSIFICATION)

        self._test_serializer_raise_validation_error(f'shopper_coupon {self.__coupon.id} is not applicable to option {self.__option.id}.')

    def test_validate_coupon_about_sub_category_coupon_classification(self):        
        self.__set_classification(SUB_CATEGORY_COUPON_CLASSIFICATION)

        self._test_serializer_raise_validation_error(f'shopper_coupon {self.__coupon.id} is not applicable to option {self.__option.id}.')

    def test_validate_coupon_about_minimum_product_price(self):        
        self.__coupon.coupon.minimum_product_price = self.__product.base_discounted_price + 1
        self.__coupon.coupon.save(update_fields=['minimum_product_price'])

        self._test_serializer_raise_validation_error(f'The price of option {self.__option.id} is lower than the minimum order price of shopper_coupon {self.__coupon.id}.')

    def test_validate_coupon_about_maximum_discount_price(self):        
        self._test_data['coupon_discount_price'] = self.__coupon.coupon.maximum_discount_price + 1

        self._test_serializer_raise_validation_error(f'coupon_discount_price has exceeded the maximum discount price of shopper_coupon {self.__coupon.id}')

    def test_validate_coupon_about_coupon_discount_price(self):        
        self._test_data['coupon_discount_price'] -= 1

        self._test_serializer_raise_validation_error(f'coupon_discount_price of option {self.__option.id} is different from the actual price.')

    def test_validated_data_for_create(self):        
        expected_data = deepcopy(self._test_data)
        expected_data['option'] = self.__option
        expected_data['shopper_coupon'] = self.__coupon
        expected_data['base_discount_price'] = expected_data['sale_price'] - expected_data['base_discounted_price']
        del expected_data['base_discounted_price']

        self._test_validated_data(expected_data)

    def test_validation_success_with_no_coupon(self):
        self._test_data = get_order_item_test_data(self.__option, self.__shopper)

        self.assertTrue(self._get_serializer_after_validation())

    def test_validation_success_with_price_coupon(self):        
        price_coupon = ShopperCouponFactory(
            shopper=self.__shopper, 
            is_used=False,
            coupon=CouponFactory(classification=self.__coupon.coupon.classification, discount_price=True)
        )
        self._test_data = get_order_item_test_data(self.__option, self.__shopper, price_coupon)

        self.assertTrue(self._get_serializer_after_validation())

    def test_validation_success_with_some_product_coupon_classification(self):        
        self.__set_classification(SOME_PRODUCT_COUPON_CLASSIFICATION)
        self.__coupon.coupon.products.add(self.__product)

        self.assertTrue(self._get_serializer_after_validation())

    def test_validation_success_with_sub_category_coupon_classification(self):        
        self.__set_classification(SUB_CATEGORY_COUPON_CLASSIFICATION)
        self.__coupon.coupon.sub_categories.add(self.__product.sub_category)

        self.assertTrue(self._get_serializer_after_validation())

    def test_validate_option_for_status(self):        
        self.__order_item.status = StatusFactory(id=1000)

        self._test_serializer_raise_validation_error('This order is in a state where options cannot be changed.', self.__order_item)

    def test_validate_option(self):        
        self._test_data = {'option': OptionFactory(product_color__product=ProductFactory(product=self.__product)).id}

        self._test_serializer_raise_validation_error('It cannot be changed to an option for another product.', self.__order_item)
    
    def test_validate_option_included_order(self):        
        self._test_serializer_raise_validation_error('This item is already included in the order.', self.__order_item, {'option': self.__option.id})

    def test_update(self):        
        option = OptionFactory(product_color__product=self.__product)
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


class OrderItemStatisticsListSerializerTestCase(ListSerializerTestCase):
    _child_serializer_class = OrderItemStatisticsSerializer

    @classmethod
    def setUpTestData(cls):
        status = [StatusFactory(id=status_id) for status_id in NORMAL_STATUS]
        cls.__test_data = [{
            'status__name': s.name,
            'count': 1,
        } for s in status]

    def __assert_serialization(self, expected_data):
        self.assertListEqual(self._get_serializer(self.__test_data).data, expected_data)

    def test_model_instance_serialization(self):
        self.__assert_serialization([self._child_serializer_class(data).data for data in self.__test_data])

    def test_to_representation(self):
        for i in range(len(self.__test_data)):
            if i % 2 == 1:
                self.__test_data[i]['count'] = 0
        expected_data = [self._child_serializer_class(data).data for data in self.__test_data]
        for i in range(len(self.__test_data) - 1, -1, -1):
            if self.__test_data[i]['count'] == 0:
                del self.__test_data[i]

        self.__assert_serialization(expected_data)


class OrderItemStatisticsSerializerTestCase(SerializerTestCase):
    _serializer_class = OrderItemStatisticsSerializer

    def setUp(self):
        self.__test_data = {
            'status__name': 'test_status',
            'count': 10,
        }

    def test_model_instance_serialization(self):
        self._test_model_instance_serialization(self.__test_data, {
            'status': self.__test_data['status__name'],
            'count': self.__test_data['count'],
        })


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
        cls.__orders = create_orders_with_items(
            order_size=3, 
            only_product_color=True, 
            order_kwargs={'shopper': ShopperFactory()}, 
            item_kwargs={'status': cls.__status, 'shopper_coupon': None}
        )
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
