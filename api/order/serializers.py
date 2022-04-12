from math import floor
from django.forms import model_to_dict

from rest_framework.serializers import (
    Serializer, ModelSerializer, ListSerializer,
    PrimaryKeyRelatedField, StringRelatedField,
    IntegerField
)
from rest_framework.exceptions import ValidationError, APIException

from common.serializers import has_duplicate_element, get_list_of_single_value, get_sum_of_single_value, add_data_in_each_element
from product.models import Option
from product.serializers import OptionInOrderItemSerializer
from .models import Order, OrderItem, ShippingAddress

# todo 전화번호 정규표현식

class ShippingAddressSerializer(ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = '__all__'

    def create(self, validated_data):
        instance = self.Meta.model.objects.get_or_create(**validated_data)[0]

        if 'order' in self.context:
            self.context['order'].shipping_address = instance
            self.context['order'].save(update_fields=['shipping_address'])

        return instance

class OrderItemListSerializer(ListSerializer):
    def validate(self, attrs):
        self.__validate_options(get_list_of_single_value('option', attrs))

        return attrs

    def __validate_options(self, value):
        if has_duplicate_element(value):
            raise ValidationError('option is duplicated.')

    def create(self, validated_data):
        OrderItem.objects.bulk_create([OrderItem(**item) for item in validated_data])


class OrderItemSerializer(ModelSerializer):
    option = OptionInOrderItemSerializer()
    earned_point = IntegerField(read_only=True)
    status = StringRelatedField()

    class Meta:
        model = OrderItem
        exclude = ['order']

    def validate(self):
        raise APIException('This serializer cannot validate.')


class OrderItemWriteSerializer(OrderItemSerializer):
    option = PrimaryKeyRelatedField(queryset=Option.objects.all())
    
    class Meta(OrderItemSerializer.Meta):
        extra_kwargs = {
            'count': {'max_value': 999, 'min_value': 1},
            'sale_price': {'min_value': 0},
            'base_discount_price': {'min_value': 0},
            'membership_discount_price': {'min_value': 0},
            'used_price': {'min_value': 0},
            'payment_price': {'min_value': 0},
        }
        list_serializer_class = OrderItemListSerializer

    def validate(self, attrs):
        if self.instance is None:
            self.__validate_price(attrs)

        return attrs


    def validate_option(self, value):
        if self.instance is None:
            return value

        if self.instance.status_id not in [101]:
            raise ValidationError('This order is in a state where options cannot be changed.')
        elif self.instance.option.product_color.product_id != value.product_color.product_id:
            raise ValidationError('It cannot be changed to an option for another product.')
        elif self.instance.option.price_difference != value.price_difference:
            raise ValidationError('It cannot be changed to an option with a different price.')

        return value


    def __validate_price(self, attrs):
        option = attrs['option']
        product = option.product_color.product

        # todo
        # product에 판매금액, 기본할인금액 등 컬럼 생기면 작업
        # if attrs['sale_price'] != product.sale_price + option.sale_price_difference:
        #     raise ValidationError('sale_price of option %d is different from the actual price.' % (option.id))
        # elif attrs['base_discount_price'] != product.base_discount_price:
        #     raise ValidationError('base_discount_price of option %d is different from the actual price.' % (option.id))
        # elif attrs['membership_discount_price'] != self.context['shopper'].membership.discount_rate:
        #     raise ValidationError('membership_discount_price of option %d is calculated incorrectly.' % (option.id))
        # elif attrs['payment_price'] != attrs['sale_price'] - attrs['base_discount_price'] - attrs['membership_discount_price']:
        #     raise ValidationError('payment_price of option %d is calculated incorrectly.' % (option.id))

    def update(self, instance, validated_data):
        for key, value in validated_data.items():            
            setattr(instance, key, value)

        instance.save(update_fields=validated_data.keys())

        return instance

class OrderSerializer(ModelSerializer):
    number = IntegerField(read_only=True)
    shipping_address = ShippingAddressSerializer()
    items = OrderItemSerializer(many=True)
    class Meta:
        model = Order
        exclude = []

    def validate(self):
        raise APIException('This serializer cannot validate.')


class OrderWriteSerializer(OrderSerializer):
    # number = IntegerField(read_only=True)
    # shipping_address = ShippingAddressSerializer()
    items = OrderItemWriteSerializer(many=True, allow_empty=False)
    actual_payment_price = IntegerField(min_value=0, write_only=True)
    used_point = IntegerField(min_value=0, required=False, write_only=True)
    earned_point = IntegerField(min_value=0, write_only=True)
    
    __validation_only_fields = ['actual_payment_price', 'used_point', 'earned_point']

    class Meta(OrderSerializer.Meta):
        exclude = ['shopper']

    def validate(self, attrs):
        if self.partial:
            return attrs
        
        self.__validate_actual_payment_price(attrs['actual_payment_price'], attrs['items'], attrs['used_point'])
        self.__validate_earned_point(attrs['earned_point'], attrs['actual_payment_price'])

        attrs['items'] = self.__get_items_including_point_information(attrs['items'], attrs['used_point'], attrs['earned_point'])

        return self.__pop_validation_only_fields(attrs)

    def __validate_actual_payment_price(self, actual_payment_price, items, used_point):
        sum_of_payment_price = get_sum_of_single_value('payment_price', items)
        
        if actual_payment_price != sum_of_payment_price - used_point:
            raise ValidationError('actual_payment_price is calculated incorrectly.')

    def __validate_earned_point(self, earned_point, actual_payment_price):
        if earned_point != floor(actual_payment_price / 100):
            raise ValidationError('earned_point is calculated incorrectly.')

    def __get_items_including_point_information(self, items, used_point, earned_point):
        total_payment_price = get_sum_of_single_value('payment_price', items)
        items = self.__distribute_point(items, 'used_point', used_point, total_payment_price)
        items = self.__distribute_point(items, 'earned_point', earned_point, total_payment_price)
        items = self.__apply_used_point_to_payment_price(items)

        return items

    def __pop_validation_only_fields(self, attrs):
        for field in self.__validation_only_fields:
            attrs.pop(field)

        return attrs

    def __distribute_point(self, items, key, point, total_payment_price):
        distributed_point = 0
        for item in items:
            item[key] = floor(item['payment_price'] * point / total_payment_price)
            distributed_point += item[key]
        
        if distributed_point != point:
            items[0][key] += point - distributed_point

        return items

    def __apply_used_point_to_payment_price(self, items):
        for item in items:
            item['payment_price'] -= item['used_point']

        return items

    def create(self, validated_data):
        items = validated_data.pop('items')
        status_id = validated_data.pop('status_id')

        validated_data['shipping_address'] = self.fields['shipping_address'].create(validated_data['shipping_address'])

        validated_data['shopper'] = self.context['shopper']
        order = self.Meta.model.objects.create(**validated_data)

        items = add_data_in_each_element(items, 'status_id', status_id)
        items = add_data_in_each_element(items, 'order', order)
        self.fields['items'].create(items)

        # todo
        # 가격, 재고 관련 작업

        return order

    
class OrderConfirmation(Serializer):
    pass
