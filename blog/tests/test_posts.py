import pytest
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext

from blog.models import Comment, Post, Tag, User


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def user(db):
    return User.objects.create(
        username="alice",
        email="alice@example.com",
        display_name="Alice",
    )


@pytest.mark.django_db
def test_list_posts_returns_published(client, user):
    tag = Tag.objects.create(name="Python", slug="python")
    post = Post.objects.create(author=user, title="Hello", body="World")
    post.tags.add(tag)
    Post.objects.create(author=user, title="Draft", body="...", is_published=False)

    response = client.get("/api/posts")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "count" in data
    assert data["count"] == 1
    titles = [p["title"] for p in data["items"]]
    assert "Hello" in titles
    assert "Draft" not in titles


@pytest.mark.django_db
def test_list_posts_pagination_count(client, user):
    for i in range(25):
        Post.objects.create(author=user, title=f"Post {i}", body="body", is_published=True)

    response = client.get("/api/posts?page=1&page_size=10")

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 25
    assert len(data["items"]) == 10

    response_page2 = client.get("/api/posts?page=2&page_size=10")
    assert len(response_page2.json()["items"]) == 10


@pytest.mark.django_db
def test_list_posts_query_count_bounded(client, user):
    tag = Tag.objects.create(name="Python", slug="python")
    for i in range(3):
        post = Post.objects.create(author=user, title=f"Hello {i}", body="World")
        post.tags.add(tag)

    with CaptureQueriesContext(connection) as context:
        response = client.get("/api/posts?page=1&page_size=20")

    assert response.status_code == 200
    assert len(response.json()["items"]) == 3
    assert len(context.captured_queries) <= 6


@pytest.mark.django_db
def test_get_post_returns_detail(client, user):
    post = Post.objects.create(author=user, title="Hello", body="World")

    response = client.get(f"/api/posts/{post.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Hello"
    assert data["author"]["username"] == "alice"
    assert data["comment_count"] == 0
    assert data["comments"] == []
    assert data["view_count"] == 1


@pytest.mark.django_db
def test_get_post_comment_pagination(client, user):
    post = Post.objects.create(author=user, title="Hello", body="World")
    for i in range(30):
        Comment.objects.create(post=post, author=user, body=f"Comment {i}")

    response = client.get(f"/api/posts/{post.id}?comment_page=1&comment_page_size=10")

    assert response.status_code == 200
    data = response.json()
    assert data["comment_count"] == 30
    assert len(data["comments"]) == 10
    assert data["comments"][0]["body"] == "Comment 0"


@pytest.mark.django_db
def test_get_post_query_count_bounded(client, user):
    post = Post.objects.create(author=user, title="Hello", body="World")
    for i in range(5):
        Comment.objects.create(post=post, author=user, body=f"Comment {i}")

    with CaptureQueriesContext(connection) as context:
        response = client.get(f"/api/posts/{post.id}?comment_page_size=5")

    assert response.status_code == 200
    assert len(response.json()["comments"]) == 5
    assert len(context.captured_queries) <= 6
