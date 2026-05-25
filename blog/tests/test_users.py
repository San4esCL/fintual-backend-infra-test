import pytest
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext

from blog.models import Comment, Post, User


@pytest.fixture
def client():
    return Client()


@pytest.mark.django_db
def test_get_user_annotated_counts(client):
    user = User.objects.create(
        username="alice",
        email="alice@example.com",
        display_name="Alice",
    )
    post = Post.objects.create(author=user, title="T1", body="B1")
    Post.objects.create(author=user, title="T2", body="B2")
    Comment.objects.create(post=post, author=user, body="Nice")

    with CaptureQueriesContext(connection) as context:
        response = client.get(f"/api/users/{user.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["post_count"] == 2
    assert data["comment_count"] == 1
    assert len(context.captured_queries) <= 2


@pytest.mark.django_db
def test_find_user_by_email(client):
    User.objects.create(
        username="alice",
        email="alice@example.com",
        display_name="Alice",
    )

    response = client.get("/api/users/find", {"email": "alice@example.com"})

    assert response.status_code == 200
    assert response.json()["username"] == "alice"
