from django.db.models import Count

from blog.models import Comment, Post, User

DEFAULT_COMMENT_PAGE_SIZE = 20
MAX_COMMENT_PAGE_SIZE = 50


def published_posts_qs():
    return (
        Post.objects.filter(is_published=True)
        .select_related("author")
        .prefetch_related("tags")
        .defer("body")
        .order_by("-created_at")
    )


def post_detail_qs():
    return (
        Post.objects.select_related("author")
        .prefetch_related("tags")
        .annotate(comment_count=Count("comments"))
    )


def comments_for_post_page(post_id: int, page: int, page_size: int):
    offset = (page - 1) * page_size
    return (
        Comment.objects.filter(post_id=post_id)
        .select_related("author")
        .order_by("created_at")[offset : offset + page_size]
    )


def normalize_comment_page_params(page: int, page_size: int | None) -> tuple[int, int]:
    page = max(page, 1)
    size = page_size if page_size is not None else DEFAULT_COMMENT_PAGE_SIZE
    size = max(1, min(size, MAX_COMMENT_PAGE_SIZE))
    return page, size


def user_detail_qs():
    return User.objects.annotate(
        post_count=Count("posts", distinct=True),
        comment_count=Count("comments", distinct=True),
    )
