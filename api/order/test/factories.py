from factory import Sequence, SubFactory, LazyAttribute
from factory.django import DjangoModelFactory
from factory.faker import Faker
from factory.fuzzy import FuzzyText, FuzzyInteger

from product.test.factories import create_options


def create_orders_with_items(order_size=1, item_size=3, only_product_color=False, order_kwargs={}, item_kwargs={}):
    orders = OrderFactory.create_batch(order_size, **order_kwargs)
    
    options = create_options(order_size * item_size, only_product_color)
    for i in range(order_size):
        for j in range(item_size):
            OrderItemFactory(order=orders[i], option=options[i * item_size + j], **item_kwargs)

    return orders


class OrderFactory(DjangoModelFactory):
    class Meta:
        model = 'order.Order'

    shopper = SubFactory('user.test.factories.ShopperFactory')
    shipping_address = SubFactory('order.test.factories.ShippingAddressFactory')


class OrderItemFactory(DjangoModelFactory):
    class Meta:
        model = 'order.OrderItem'

    order = SubFactory(OrderFactory)
    option = SubFactory('product.test.factories.OptionFactory')
    status = SubFactory('order.test.factories.StatusFactory')
    count = FuzzyInteger(1, 5)
    sale_price = LazyAttribute(lambda obj: obj.option.product_color.product.sale_price * obj.count)
    base_discount_price = LazyAttribute(lambda obj: (obj.option.product_color.product.sale_price - obj.option.product_color.product.base_discounted_price) * obj.count)
    membership_discount_price = LazyAttribute(lambda obj: obj.option.product_color.product.base_discounted_price * obj.order.shopper.membership.discount_rate // 100 * obj.count)
    payment_price = LazyAttribute(lambda obj: obj.sale_price - obj.base_discount_price - obj.membership_discount_price)
    earned_point = LazyAttribute(lambda obj: obj.payment_price // 100)


class StatusFactory(DjangoModelFactory):
    class Meta:
        model = 'order.Status'

    id = Sequence(lambda num: num)
    name = FuzzyText()


class StatusHistoryFactory(DjangoModelFactory):
    class Meta:
        model = 'order.StatusHistory'

    order_item = SubFactory(OrderItemFactory)
    status = LazyAttribute(lambda obj: obj.order_item.status)


class ShippingAddressFactory(DjangoModelFactory):
    class Meta:
        model = 'order.ShippingAddress'

    receiver_name = Faker('name', locale='ko-KR')
    mobile_number = Sequence(lambda num: '010%08d' % num)
    phone_number = Sequence(lambda num: '02%08d' % num)
    zip_code = Faker('postcode', locale='ko-KR')
    base_address = Faker('address', locale='ko-KR')
    detail_address = Faker('address_detail', locale='ko-KR')
    shipping_message = '부재 시 집 앞에 놔주세요.'


class RefundFactory(DjangoModelFactory):
    class Meta:
        model = 'order.Refund'
    
    price = FuzzyInteger(1000, 5000000)


class DeliveryFactory(DjangoModelFactory):
    class Meta:
        model = 'order.Delivery'
    
    company = Faker('company', locale='ko-KR')
    invoice_number = Sequence(lambda num: '%015d' % num)
    flag = FuzzyText()