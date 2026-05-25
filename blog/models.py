from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.db.models import Q
from django.utils import timezone


class User(models.Model):
    username = models.CharField(max_length=64, unique=True)
    email = models.CharField(max_length=255)
    display_name = models.CharField(max_length=128)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["email"], name="blog_user_email_idx"),
        ]

    def __str__(self) -> str:
        return self.username


class Tag(models.Model):
    name = models.CharField(max_length=64, unique=True)
    slug = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return self.name


class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    title = models.CharField(max_length=255)
    body = models.TextField()
    is_published = models.BooleanField(default=True)
    view_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    tags = models.ManyToManyField(Tag, related_name="posts", blank=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["-created_at"],
                condition=Q(is_published=True),
                name="blog_post_pub_created_desc_idx",
            ),
            GinIndex(
                fields=["title"],
                name="blog_post_title_trgm_idx",
                opclasses=["gin_trgm_ops"],
            ),
            GinIndex(
                fields=["body"],
                name="blog_post_body_trgm_idx",
                opclasses=["gin_trgm_ops"],
            ),
        ]

    def __str__(self) -> str:
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    body = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
