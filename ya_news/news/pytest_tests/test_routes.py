from http import HTTPStatus

import pytest

from django.test import Client
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from news.models import News, Comment
from django.contrib.auth import get_user_model

User = get_user_model()

"""Создание данных для тестов(ФИКСТУР)"""


@pytest.fixture
def author():
    return User.objects.create(username='Автор')


@pytest.fixture
def reader():
    return User.objects.create(username='Читатель')


@pytest.fixture
def author_client(author):
    client = Client()
    client.force_login(author)
    return client


@pytest.fixture
def reader_client(reader):
    client = Client()
    client.force_login(reader)
    return client


@pytest.fixture
def news():
    return News.objects.create(title='Заголовок', text='Текст новости')


@pytest.fixture
def comment(author, news):
    return Comment.objects.create(
        news=news,
        author=author,
        text='Текст комментария'
    )


@pytest.fixture
def news_id(news):
    return (news.id,)


@pytest.fixture
def comment_id(comment):
    return (comment.id,)


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name, args',
    [
        ('news:home', None),
        ('users:login', None),
        ('users:logout', None),
        ('users:signup', None),
        ('news:detail', pytest.lazy_fixture('news_id')),
    ]
)
def test_pages_availability_for_anonymous(client, name, args):
    """Проверка доступности страниц для анонимных пользователей."""
    url = reverse(name, args=args)
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name',
    ('news:edit', 'news:delete')
)
def test_author_access(author_client, comment_id, name):
    """Проверка доступа автора к страницам
    редактирования и удаления комментария.
    """
    url = reverse(name, args=comment_id)
    response = author_client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name',
    ('news:edit', 'news:delete')
)
def test_other_users_access(reader_client, comment_id, name):
    """Проверка, другие пользователи не могут получить доступ к страницам
    редактирования и удаления комментария.
    """
    url = reverse(name, args=comment_id)
    response = reader_client.get(url)
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name',
    ('news:edit', 'news:delete')
)
def test_anonymous_redirect(client, comment_id, name):
    """Проверка, что анонимный пользователь перенаправляется на страницу входа
    при попытке доступа к страницам редактирования и удаления комментария.
    """
    login_url = reverse('users:login')
    url = reverse(name, args=comment_id)
    redirect_url = f'{login_url}?next={url}'
    response = client.get(url)
    assertRedirects(response, redirect_url)
