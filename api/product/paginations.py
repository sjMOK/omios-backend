from rest_framework.pagination import PageNumberPagination


class ProductQuestionAnswerPagination(PageNumberPagination):
    page_size = 10