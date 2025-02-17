from http import HTTPStatus

from pytest_django.asserts import assertRedirects
import pytest


@pytest.mark.django_db
@pytest.mark.parametrize(
    'url',
    [
        pytest.lazy_fixture('home_url'),
        pytest.lazy_fixture('login_url'),
        pytest.lazy_fixture('logout_url'),
        pytest.lazy_fixture('signup_url'),
        pytest.lazy_fixture('detail_url'),
    ]
)
def test_public_pages_availability(client, url):
    """Проверка доступности публичных страниц."""
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
@pytest.mark.parametrize(
    'url',
    [
        pytest.lazy_fixture('edit_url'),
        pytest.lazy_fixture('delete_url'),
    ]
)
def test_author_access(author_client, url):
    """Проверка доступа автора к страницам
    редактирования и удаления комментария.
    """
    response = author_client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
@pytest.mark.parametrize(
    'url',
    [
        pytest.lazy_fixture('edit_url'),
        pytest.lazy_fixture('delete_url'),
    ]
)
def test_other_users_access(reader_client, url):
    """Проверка, другие пользователи не могут получить доступ к страницам
    редактирования и удаления комментария.
    """
    response = reader_client.get(url)
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
@pytest.mark.parametrize(
    'url',
    [
        pytest.lazy_fixture('edit_url'),
        pytest.lazy_fixture('delete_url'),
    ]
)
def test_anonymous_redirect(client, url, login_url):
    """Проверка, что анонимный пользователь перенаправляется на страницу входа
    при попытке доступа к страницам редактирования и удаления комментария.
    """
    redirect_url = f'{login_url}?next={url}'
    response = client.get(url)
    assertRedirects(response, redirect_url)
