from rest_framework.pagination import PageNumberPagination


class PointHistoryPagination(PageNumberPagination):
    page_size = 20