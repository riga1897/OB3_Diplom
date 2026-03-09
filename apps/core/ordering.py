"""Кастомные классы фильтрации с русскими описаниями."""

from rest_framework.filters import OrderingFilter, SearchFilter


class RussianOrderingFilter(OrderingFilter):
    """Фильтр сортировки с русскими описаниями."""

    ordering_description = (
        "Поле для сортировки результатов. Используйте '-' для сортировки по убыванию."
    )


class RussianSearchFilter(SearchFilter):
    """Фильтр поиска с русскими описаниями."""

    search_description = "Поисковый запрос для фильтрации результатов."
