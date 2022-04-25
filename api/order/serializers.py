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
from .models import Order, OrderItem, ShippingAddress, Refund, CancellationInformation

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
        self.__validate_options(get_list_of_single_value(attrs, 'option'))

        return attrs

    def __validate_options(self, value):
        if has_duplicate_element(value):
            raise ValidationError('option is duplicated.')

    def create(self, validated_data):
        self.child.Meta.model.objects.bulk_create([OrderItem(**item) for item in validated_data])

    def __set_claim(self, item, claim, claim_field):
        setattr(item, claim_field, claim)
        if isinstance(claim, CancellationInformation):
            if claim.refund is None:
                item.status_id = 102
            else:
                item.status_id = 103

    def update(self, queryset, claim_field):
        if claim_field == 'cancellation_information':
            serializer = CancellationInformationSerializer()


        # todo
        # try catch?

        for item in queryset:
            # instance = serializer.create({'item': item})
            # setattr(item, update_field, instance)
            # item.save(update_fields=[update_field])

            self.__set_claim(item, serializer.create({'item': item}), claim_field)
            item.save(update_fields=[claim_field, 'status'])

        return queryset


class OrderItemSerializer(ModelSerializer):
    option = OptionInOrderItemSerializer()
    base_discount_price = IntegerField(read_only=True)
    earned_point = IntegerField(read_only=True)
    status = StringRelatedField()

    class Meta:
        model = OrderItem
        exclude = ['order']

    def validate(self):
        raise APIException('This serializer cannot validate.')


class OrderItemWriteSerializer(OrderItemSerializer):
    option = PrimaryKeyRelatedField(queryset=Option.objects.select_related('product_color__product').all())
    base_discounted_price = IntegerField()

    class Meta(OrderItemSerializer.Meta):
        extra_kwargs = {
            'count': {'max_value': 999, 'min_value': 1},
            'sale_price': {'min_value': 0},
            'membership_discount_price': {'min_value': 0},
            'used_price': {'min_value': 0},
            'payment_price': {'min_value': 0},
        }
        list_serializer_class = OrderItemListSerializer

    def validate(self, attrs):
        if self.instance is not None:
            return attrs

        self.__validate_price(attrs)

        return attrs


    def validate_option(self, value):
        if self.instance is None:
            return value

        if self.instance.status_id not in [100, 101]:
            raise ValidationError('This order is in a state where options cannot be changed.')
        elif self.instance.option.product_color.product_id != value.product_color.product_id:
            raise ValidationError('It cannot be changed to an option for another product.')

        return value

    def __validate_price(self, attrs):
        option = attrs['option']
        product = option.product_color.product

        if attrs['sale_price'] != product.sale_price:
            raise ValidationError(f'sale_price of option {option.id} is different from the actual price.')
        elif attrs['base_discounted_price'] != product.base_discounted_price:
            raise ValidationError(f'base_discounted_price of option {option.id} is different from the actual price.')
        elif attrs['membership_discount_price'] != attrs['base_discounted_price'] * self.context['shopper'].membership.discount_rate // 100:
            raise ValidationError(f'membership_discount_price of option {option.id} is different from the actual price.')
        # todo 쿠폰 validation
        elif attrs['payment_price'] != attrs['base_discounted_price'] - attrs['membership_discount_price']:
            raise ValidationError(f'payment_price of option {option.id} is different from the actual price.')

        attrs['base_discount_price'] = attrs['sale_price'] - attrs['base_discounted_price']
        attrs.pop('base_discounted_price')

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
    
    class Meta(OrderSerializer.Meta):
        exclude = ['shopper']

    def validate(self, attrs):
        if self.instance is not None:
            return attrs

        self.__validate_price(attrs)

        return attrs

    def __validate_price(self, attrs):
        total_payment_price = get_sum_of_single_value(attrs['items'], 'payment_price')
        if attrs['actual_payment_price'] != total_payment_price - attrs['used_point']:
            raise ValidationError('actual_payment_price is calculated incorrectly.')
        elif attrs['used_point'] > self.context['shopper'].point:
            raise ValidationError('The shopper has less point than used_point.')
        elif attrs['earned_point'] != attrs['actual_payment_price'] // 100:
            raise ValidationError('earned_point is calculated incorrectly.')
        
        self.__set_items_including_point_informations2(attrs['items'], attrs['used_point'], attrs['earned_point'], total_payment_price)

        attrs.pop('actual_payment_price')
        attrs.pop('earned_point')

    def __set_items_including_point_informations2(self, items, used_point, earned_point, total_payment_price):
        self.__distribute_point(items, 'used_point', used_point, total_payment_price)
        self.__distribute_point(items, 'earned_point', earned_point, total_payment_price)
        self.__apply_used_point_to_payment_price(items)

    def __distribute_point(self, items, key, point, total_payment_price):
        distributed_point = 0
        for item in items:
            item[key] = floor(item['payment_price'] * point / total_payment_price)
            distributed_point += item[key]
        
        if distributed_point != point:
            items[0][key] += point - distributed_point

    def __apply_used_point_to_payment_price(self, items):
        for item in items:
            item['payment_price'] -= item['used_point']

    def create(self, validated_data):
        shopper = self.context['shopper']
        used_point = validated_data.pop('used_point')
        items = validated_data.pop('items')
        status_id = validated_data.pop('status_id')
    
        validated_data['shipping_address'] = self.fields['shipping_address'].create(validated_data['shipping_address'])

        validated_data['shopper'] = shopper
        order = self.Meta.model.objects.create(**validated_data)

        items = add_data_in_each_element(items, 'status_id', status_id)
        items = add_data_in_each_element(items, 'order', order)
        self.fields['items'].create(items)

        shopper.update_point(-1 * used_point, '적립금 결제', order)

        # todo
        # 가격, 재고 관련 작업

        return order

    
class OrderConfirmation(Serializer):
    pass


class RefundSerializer(ModelSerializer):
    class Meta:
        model = Refund
        fields = '__all__'


class CancellationInformationSerializer(ModelSerializer):
    refund = RefundSerializer(required=False)

    class Meta:
        model = CancellationInformation
        fields = '__all__'

    def create(self, validated_data):
        item = validated_data['item']

        refund = None
        if item.status_id == 101:
            refund = self.fields['refund'].create({'price': item.payment_price})

        return self.Meta.model.objects.create(refund=refund)
