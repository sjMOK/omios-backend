from django.urls import path

from .views import StatusHistoryAPIView

app_name = 'order'

urlpatterns = [
    path('/items/<int:item_id>/status-histories', StatusHistoryAPIView.as_view()),
]