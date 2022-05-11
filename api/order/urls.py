from django.urls import path

from rest_framework.routers import SimpleRouter

from .documentations import DecoratedOrderItemViewSet, DecoratedClaimViewset, decorated_status_history_view

app_name = 'order'

router = SimpleRouter(trailing_slash=False)
router.register(r'/items', DecoratedOrderItemViewSet, 'order-items')
router.register(r'/(?P<order_id>\d+)', DecoratedClaimViewset, 'order-claim')

urlpatterns = [
    path('/items/<int:item_id>/status-histories', decorated_status_history_view),
]

urlpatterns += router.urls