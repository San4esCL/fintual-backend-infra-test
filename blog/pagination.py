from ninja.pagination import PageNumberPagination

from blog.serializers import serialize_post_list


class PostPageNumberPagination(PageNumberPagination):
    page_size = 20
    max_page_size = 100

    def paginate_queryset(self, queryset, pagination, request, **params):
        page_size = self._get_page_size(pagination.page_size)
        offset = (pagination.page - 1) * page_size
        page = queryset[offset : offset + page_size]
        return {
            self.items_attribute: [serialize_post_list(post) for post in page],
            "count": self._items_count(queryset),
        }
