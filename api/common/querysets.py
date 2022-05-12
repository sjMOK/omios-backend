from django.db.models.query import Prefetch

from product.models import ProductImage
from order.models import Order, OrderItem


def get_order_item_queryset():
    images = ProductImage.objects.filter(sequence=1)
    return OrderItem.objects.select_related('option__product_color__product', 'status'). \
        prefetch_related(Prefetch('option__product_color__product__images', images))


def get_order_queryset():
    return Order.objects.select_related('shipping_address'). \
        prefetch_related(Prefetch('items', get_order_item_queryset()))