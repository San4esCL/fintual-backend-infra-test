from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import F
from django.shortcuts import get_object_or_404
from ninja import Query, Router
from ninja.pagination import paginate

from blog.models import Comment, Post, Tag, User
from blog.pagination import PostPageNumberPagination
from blog.queries import (
    comments_for_post_page,
    normalize_comment_page_params,
    post_detail_qs,
    published_posts_qs,
    user_detail_qs,
)
from blog.schemas import (
    CommentCreateIn,
    CommentCreateOut,
    PostCreateIn,
    PostCreateOut,
    PostDetailOut,
    PostListOut,
    UserDetailOut,
)
from blog.serializers import serialize_author, serialize_tag

router = Router()

SEARCH_SIMILARITY_THRESHOLD = 0.1


@router.get("/posts", response=list[PostListOut])
@paginate(PostPageNumberPagination)
def list_posts(request):
    return published_posts_qs()


@router.get("/posts/search", response=list[PostListOut])
@paginate(PostPageNumberPagination)
def search_posts(request, q: str):
    return (
        published_posts_qs()
        .annotate(
            similarity=TrigramSimilarity("title", q) + TrigramSimilarity("body", q),
        )
        .filter(similarity__gt=SEARCH_SIMILARITY_THRESHOLD)
        .order_by("-similarity", "-created_at")
    )


@router.get("/posts/by-tag/{slug}", response=list[PostListOut])
@paginate(PostPageNumberPagination)
def posts_by_tag(request, slug: str):
    tag = get_object_or_404(Tag, slug=slug)
    return published_posts_qs().filter(tags=tag)


@router.get("/posts/{post_id}", response=PostDetailOut)
def get_post(
    request,
    post_id: int,
    comment_page: int = Query(1, ge=1),
    comment_page_size: int | None = Query(None, ge=1),
):
    post = get_object_or_404(post_detail_qs(), pk=post_id)
    Post.objects.filter(pk=post_id).update(view_count=F("view_count") + 1)

    page, page_size = normalize_comment_page_params(comment_page, comment_page_size)
    comments = [
        {
            "id": c.id,
            "author": serialize_author(c.author),
            "body": c.body,
            "created_at": c.created_at,
        }
        for c in comments_for_post_page(post_id, page, page_size)
    ]
    return {
        "id": post.id,
        "title": post.title,
        "body": post.body,
        "author": serialize_author(post.author),
        "tags": [serialize_tag(t) for t in post.tags.all()],
        "comment_count": post.comment_count,
        "comments": comments,
        "view_count": post.view_count + 1,
        "created_at": post.created_at,
        "updated_at": post.updated_at,
    }


@router.post("/posts", response=PostCreateOut)
def create_post(request, payload: PostCreateIn):
    author = get_object_or_404(User, id=payload.author_id)
    post = Post.objects.create(
        author=author,
        title=payload.title,
        body=payload.body,
    )
    for slug in payload.tag_slugs:
        tag = Tag.objects.get(slug=slug)
        post.tags.add(tag)
    return {"id": post.id, "title": post.title}


@router.post("/posts/{post_id}/comments", response=CommentCreateOut)
def create_comment(request, post_id: int, payload: CommentCreateIn):
    post = get_object_or_404(Post, id=post_id)
    author = get_object_or_404(User, id=payload.author_id)
    comment = Comment.objects.create(post=post, author=author, body=payload.body)
    return {"id": comment.id}


@router.get("/users/find", response=UserDetailOut)
def find_user_by_email(request, email: str):
    user = get_object_or_404(user_detail_qs(), email=email)
    return _user_detail(user)


@router.get("/users/{user_id}", response=UserDetailOut)
def get_user(request, user_id: int):
    user = get_object_or_404(user_detail_qs(), pk=user_id)
    return _user_detail(user)


def _user_detail(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "email": user.email,
        "bio": user.bio,
        "post_count": user.post_count,
        "comment_count": user.comment_count,
    }
