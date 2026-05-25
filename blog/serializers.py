from blog.models import Post, Tag, User


def serialize_author(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
    }


def serialize_tag(tag: Tag) -> dict:
    return {"id": tag.id, "name": tag.name, "slug": tag.slug}


def serialize_post_list(post: Post) -> dict:
    return {
        "id": post.id,
        "title": post.title,
        "author": serialize_author(post.author),
        "tags": [serialize_tag(tag) for tag in post.tags.all()],
        "view_count": post.view_count,
        "created_at": post.created_at,
    }
