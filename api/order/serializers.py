import random
import string
from dateutil.relativedelta import relativedelta

from django.utils import timezone

from rest_framework.serializers import (
    Serializer, ModelSerializer, ListSerializer,
    PrimaryKeyRelatedField, StringRelatedField,
    IntegerField, ListField, CharField,
)
from rest_framework.exceptions import ValidationError

from common.serializers import (
    has_duplicate_element, get_list_of_single_value, get_sum_of_single_value, add_data_in_each_element,
    get_list_of_multi_values,
)
from common.exceptions import NotExcutableValidationError
from common.utils import DATETIME_WITHOUT_MILISECONDS_FORMAT
from product.models import Option
from product.serializers import OptionInOrderItemSerializer
from .models import (
    PAYMENT_COMPLETION_STATUS, DELIVERY_PREPARING_STATUS, DELIVERY_PROGRESSING_STATUS, BEFORE_DELIVERY_STATUS, NORMAL_STATUS,
    Order, OrderItem, Status, ShippingAddress, Refund, CancellationInformation, StatusHistory,
    ExchangeInformation, Delivery
)
from .validators import validate_order_items


ORDER_MAXIMUM_NUMBER = 100


class ShippingAddressSerializer(ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = '__all__'

    def validate(self, attrs):
        if 'order' in self.context:
            self.__validate_status()

        return attrs

    # todo test code 작성
    def __validate_status(self):
        if self.context['order'].items.exclude(status__in=BEFORE_DELIVERY_STATUS).exists():
            raise ValidationError('The shipping address for this order cannot be changed.')

    def create(self, validated_data):
        instance = self.Meta.model.objects.get_or_create(**validated_data)[0]

        if 'order' in self.context:
            self.context['order'].shipping_address = instance
            self.context['order'].save(update_fields=['shipping_address'])

        return instance


class OrderItemSerializer(ModelSerializer):
    option = OptionInOrderItemSerializer()
    base_discount_price = IntegerField(read_only=True)
    earned_point = IntegerField(read_only=True)
    used_point = IntegerField(read_only=True)
    status = StringRelatedField()

    class Meta:
        model = OrderItem
        exclude = ['order']

    def validate(self, attrs):
        raise NotExcutableValidationError()


class OrderItemListSerializer(ListSerializer):
    def validate(self, attrs):
        self.__validate_options(get_list_of_single_value(attrs, 'option'))

        return attrs

    def __validate_options(self, value):
        if has_duplicate_element(value):
            raise ValidationError('option is duplicated.')

    def __create_status_history(self, queryset):
        return StatusHistorySerializer().create(queryset)

    def create(self, validated_data):
        model = self.child.Meta.model
        model.objects.bulk_create([model(**item) for item in validated_data])
        
        queryset = model.objects.filter(order=validated_data[0]['order'])
        self.__create_status_history(queryset)

        return queryset

    def update_status(self, queryset, status_id):
        for instance in queryset:
            instance.status_id = status_id

        self.child.Meta.model.objects.bulk_update(queryset, ['status_id'])
        self.__create_status_history(queryset)

        return queryset


class OrderItemWriteSerializer(OrderItemSerializer):
    option = PrimaryKeyRelatedField(queryset=Option.objects.select_related('product_color__product').all())
    base_discounted_price = IntegerField(min_value=0)

    class Meta(OrderItemSerializer.Meta):
        extra_kwargs = {
            'count': {'max_value': 999, 'min_value': 1, 'required': True},
            'sale_price': {'min_value': 0},
            'membership_discount_price': {'min_value': 0},
            # 'used_price': {'min_value': 0},
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

        if self.instance.status_id not in BEFORE_DELIVERY_STATUS:
            raise ValidationError('This order is in a state where options cannot be changed.')
        elif self.instance.option.product_color.product_id != value.product_color.product_id:
            raise ValidationError('It cannot be changed to an option for another product.')
        elif OrderItem.objects.filter(order=self.instance.order, option=value).exists():
            raise ValidationError('This item is already included in the order.')

        return value

    def __validate_price(self, attrs):
        option = attrs['option']
        product = option.product_color.product

        if attrs['sale_price'] != product.sale_price * attrs['count']:
            raise ValidationError(f'sale_price of option {option.id} is different from the actual price.')
        elif attrs['base_discounted_price'] != product.base_discounted_price * attrs['count']:
            raise ValidationError(f'base_discounted_price of option {option.id} is different from the actual price.')
        elif attrs['membership_discount_price'] != product.base_discounted_price * self.context['shopper'].membership.discount_rate // 100 * attrs['count']:
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
    shipping_address = ShippingAddressSerializer()
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        exclude = []
        extra_kwargs = {
            'number': {'read_only': True}
        }

    def validate(self, attrs):
        raise NotExcutableValidationError()


class OrderWriteSerializer(OrderSerializer):
    items = OrderItemWriteSerializer(many=True, allow_empty=False)
    actual_payment_price = IntegerField(min_value=1000, write_only=True)
    used_point = IntegerField(min_value=0, write_only=True)
    earned_point = IntegerField(min_value=0, write_only=True)
    
    class Meta(OrderSerializer.Meta):
        exclude = ['shopper']

    def validate(self, attrs):
        if self.instance is not None:
            raise NotExcutableValidationError()

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
        
        self.__set_items_including_point_informations(attrs['items'], attrs['used_point'], attrs['earned_point'], total_payment_price)

        attrs.pop('actual_payment_price')
        attrs.pop('earned_point')

    def __set_items_including_point_informations(self, items, used_point, earned_point, total_payment_price):
        self.__distribute_point(items, 'used_point', used_point, total_payment_price)
        self.__distribute_point(items, 'earned_point', earned_point, total_payment_price)
        self.__apply_used_point_to_payment_price(items)

    def __distribute_point(self, items, key, point, total_payment_price):
        distributed_point = 0
        for item in items:
            item[key] = int(item['payment_price'] * point / total_payment_price)
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

        shopper.update_point(-1 * used_point, '적립금으로 결제', order.id)

        # todo
        # 가격, 재고 관련 작업
        # transaction

        # 교환 주문 생성 시 로직 분리

        return order

    def update_shipping_address(self, instance, shipping_address_id):
        pass


class OrderItemStatisticsListSerializer(ListSerializer):
    def to_representation(self, data):
        result = super().to_representation(data)

        if len(result) < 6:
            status_names = Status.objects.filter(id__in=NORMAL_STATUS).order_by('id').values_list('name', flat=True)
            for i in range(len(status_names)):
                if i == len(result) or result[i]['status'] != status_names[i]:
                    result.insert(i, self.child.to_representation({'status__name': status_names[i], 'count': 0}))
        
        return result
            

class OrderItemStatisticsSerializer(Serializer):
    class Meta:
        list_serializer_class = OrderItemStatisticsListSerializer

    status = CharField(read_only=True, source='status__name')
    count = IntegerField(read_only=True)


class RefundSerializer(ModelSerializer):
    class Meta:
        model = Refund
        fields = '__all__'


class OrderItemClaimSerializer(Serializer):
    order_items = PrimaryKeyRelatedField(queryset=OrderItem.objects.all(), many=True)


# todo test code 작성
# claim(교환, 반품, 취소) 관련 설계 끝난 이후
class CancellationInformationSerializer(ModelSerializer):
    order_items = PrimaryKeyRelatedField(queryset=OrderItem.objects.select_related('order', 'option__product_color__product').all(), many=True, allow_empty=False, write_only=True)
    refund = RefundSerializer(read_only=True)

    class Meta:
        model = CancellationInformation
        fields = '__all__'
        extra_kwargs = {
            'order_item': {'read_only': True},
        }

    def validate_order_items(self, value):
        validation_set = list(set([(order_item.order.shopper_id, order_item.order_id, order_item.status_id) for order_item in value]))
        if len(validation_set) != 1:
            raise ValidationError('You can only make a request for one shopper, for one order, and for order items that are all in the same status.')
        elif validation_set[0][0] != self.context['shopper'].user_id:
            raise ValidationError('You can only request your own order.')
        elif validation_set[0][1] != self.context['order_id']:
            raise ValidationError('The order requested and the order items are different.')
        elif validation_set[0][2] not in self.context['status_id']:
            raise ValidationError('The order_items cannot be requested.')

        return value

    def __recover_point(self, order_items):
        total_used_point = 0
        details = []
        for order_item in order_items:
            total_used_point += order_item.used_point
            details.append({
                'point': order_item.used_point, 
                'prduct_name': order_item.option.product_color.product.name
            })

        self.context['shopper'].update_point(total_used_point, '주문 취소로 인한 사용 포인트 복구', details)

    def __set_refund(self, validated_data, payment_price):
        refund = self.fields['refund'].create({'price': payment_price})
        
        return [{**data, 'refund': refund} for data in validated_data]

    # 취소 데이터 생성
    def create(self, validated_data):
        order_items = validated_data['order_items']

        if order_items[0].status_id == 101:
            update_status_id = 103
        else:
            update_status_id = 102

        # total_used_point = 0
        # order_items_to_recover_point = []
        # datas_for_creation = []
        # for order_item in order_items:
        #     data = {'order_item': order_item}
        #     if order_item.status_id == 101:
        #         # todo 환불 (한번에)
        #         # 쿠폰 재발급
        #         order_item.status_id = 103
        #         data['refund'] = self.fields['refund'].create({'price': order_item.payment_price})
        #     else:
        #         order_item.status_id = 102
            
        #     datas_for_creation.append(data)

        #     total_used_point += order_item.used_point
        #     order_items_to_recover_point.append({'point': order_item.used_point, 'product_name': order_item.option.product_color.product.name})

        
        # transaction
        validated_data = [{'order_item': order_item} for order_item in order_items]
        if update_status_id == 103:
            validated_data = self.__set_refund(validated_data)        

        # OrderItemWriteSerializer(many=True).update(order_items, ['status_id'])
        OrderItemWriteSerializer(many=True).update_status(order_items, update_status_id)
        self.__recover_point(order_items)
        # self.context['shopper'].update_point(total_used_point, '주문 취소로 인한 사용 포인트 복구', self.context['order_id'], order_items_to_recover_point)

        model = self.Meta.model
        # return model.objects.bulk_create([model(**data) for data in datas_for_creation])     
        return model.objects.bulk_create([model(**data) for data in validated_data])


class StatusHistorySerializer(ModelSerializer):
    status = StringRelatedField()

    class Meta:
        model = StatusHistory
        exclude = ['order_item']

    def create(self, order_items):
        model = self.Meta.model
        return model.objects.bulk_create([model(order_item=order_item, status_id=order_item.status_id) for order_item in order_items])


class OrderConfirmSerializer(Serializer):
    order_items = ListField(child=IntegerField(), max_length=100, allow_empty=False)

    def validate_order_items(self, value):
        if has_duplicate_element(value):
            raise ValidationError('order_item is duplicated.')

        requested_order_items = OrderItem.objects.select_for_update().filter(id__in=value)
        requested_order_items_id = requested_order_items.values_list('id', flat=True)

        self.__nonexistence = sorted(set(value).difference(requested_order_items_id))
        self.__not_requestable_status = list(requested_order_items_id.exclude(status_id=PAYMENT_COMPLETION_STATUS))

        return requested_order_items.filter(status_id=PAYMENT_COMPLETION_STATUS)

    def create(self, validated_data):
        order_items = validated_data['order_items']

        success = list(order_items.values_list('id', flat=True))
        OrderItemWriteSerializer(many=True).update_status(order_items, DELIVERY_PREPARING_STATUS)

        return {
            'success': success,
            'nonexistence': self.__nonexistence,
            'not_requestable_status': self.__not_requestable_status,
        }


# 요청 데이터 안에서의 중복은 아무것도 처리하지 않고 에러 반환
# 이미 DB에 존재하는 등의 에러는 결과에 포함시키고 나머지 정상 아이템에 대해서만 처리
class DeliveryListSerializer(ListSerializer):
    def validate(self, attrs):
        self.__validate_orders_and_items(attrs)
        self.__validate_company_and_invoice_number(attrs)

        return attrs

    def __set_failure_result(self, attrs, key):
        result = []
        for i in range(len(attrs) - 1, -1, -1):
            if attrs[i].get(key, True) is None:
                result.insert(0, attrs.pop(i)['order'])
        
        if key == 'order_items':
            self.__invalid_orders = result
        elif key == 'is_valid_invoice':
            self.__existed_invoice = result

    def __validate_orders_and_items(self, attrs):
        if has_duplicate_element(get_list_of_single_value(attrs, 'order')):
            raise ValidationError('order is duplicated.')

        self.__set_failure_result(attrs, 'order_items')

    def __validate_company_and_invoice_number(self, attrs):
        if has_duplicate_element(get_list_of_multi_values(attrs, 'company', 'invoice_number')):
            raise ValidationError('invoice_number is duplicated.')

        self.__set_failure_result(attrs, 'is_valid_invoice')

    def create(self, validated_data):
        flag = timezone.now().strftime(DATETIME_WITHOUT_MILISECONDS_FORMAT) + ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(5, 10)))
        model = self.child.Meta.model
        model.objects.bulk_create([model(company=data['company'], invoice_number=data['invoice_number'], flag=flag) for data in validated_data])
        deliveries = model.objects.filter(flag=flag)

        order_items = []
        for delivery in deliveries:
            data = next((data for data in validated_data if data['company'] == delivery.company and data['invoice_number'] == delivery.invoice_number), False)
            for order_item in data['order_items']:
                order_item.delivery = delivery
                order_items.append(order_item)

        OrderItem.objects.bulk_update(order_items, ['delivery'])
        OrderItemWriteSerializer(many=True).update_status(order_items, DELIVERY_PROGRESSING_STATUS)

        return {
            'success': [data['order'] for data in validated_data],
            'invalid_orders': self.__invalid_orders,
            'existed_invoice': self.__existed_invoice,
        }


class DeliverySerializer(ModelSerializer):
    order = IntegerField()
    order_items = ListField(child=IntegerField(), allow_empty=False)

    class Meta:
        model = Delivery
        exclude = ['flag']
        list_serializer_class = DeliveryListSerializer

    def validate(self, attrs):
        self.__validate_order_and_items(attrs)
        self.__validate_company_and_invoice_number(attrs)

        return attrs

    def __validate_order_and_items(self, attrs):
        order = attrs['order']
        order_items = attrs['order_items']
        if has_duplicate_element(order_items):
            raise ValidationError(f'order_item of order {order} is duplicated.')

        requested_order_items = OrderItem.objects.select_for_update() \
            .filter(id__in=order_items, order_id=order, status_id=DELIVERY_PREPARING_STATUS, delivery_id=None)
        
        if len(requested_order_items) != len(order_items):
            attrs['order_items'] = None
        else:
            attrs['order_items'] = requested_order_items

    def __validate_company_and_invoice_number(self, attrs):
        requested_delivery = Delivery.objects.select_for_update() \
            .filter(company=attrs['company'], invoice_number=attrs['invoice_number'], created_at__gte=timezone.now() - relativedelta(months=3))
        
        if requested_delivery.exists():
            attrs['is_valid_invoice'] = None



# 적림금 사용 0원일 때 history 저장 x
# 기간 별 주문 조회, 상태별 추가 정보(클레임 정보), 주문 조회 시 페이지네이션
# 각 상태별 주문 개수


# DevlierySerializer 성능 개선, orderviewset으로 이동
