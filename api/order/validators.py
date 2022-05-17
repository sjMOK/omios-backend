from rest_framework.validators import ValidationError

from common.serializers import has_duplicate_element


def validate_order_items(order_items, order_id=None, status_ids=None):
    validation_set = list(set([(order_item.order_id, order_item.status_id) for order_item in order_items]))
    if has_duplicate_element(order_items):
        raise ValidationError('order_item is duplicated.')
    elif len(validation_set) != 1:
        raise ValidationError('You can only make a request for one order and for order items that are all in the same status.')
    elif order_id is not None and validation_set[0][0] != order_id:
        raise ValidationError('The order requested and the order items are different.')
    elif status_ids is not None and validation_set[0][1] not in status_ids:
        raise ValidationError('The order_items cannot be requested.')