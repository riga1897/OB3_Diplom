"""Кастомные классы пагинации с русскими описаниями."""

from rest_framework.pagination import PageNumberPagination


class RussianPageNumberPagination(PageNumberPagination):
    """Пагинация с русскими описаниями параметров."""

    page_query_param = "page"
    page_query_description = "Номер страницы в разбитом на страницы наборе результатов."
    page_size_query_param = "page_size"
    page_size_query_description = "Количество результатов на странице."
    max_page_size = 100
