from http import HTTPStatus

from pytest_django.asserts import assertFormError, assertRedirects
import pytest

from news.forms import BAD_WORDS, WARNING
from news.models import Comment


@pytest.mark.django_db
def test_anonymous_cant_create_comment(client, form_data, news, detail_url):
    """Проверка, анонимный пользователь не может создать комментарий."""
    client.post(detail_url, data=form_data)
    comments_count = Comment.objects.count()
    assert comments_count == 0


@pytest.mark.django_db
def test_user_can_create_comment(
    author_client, form_data, news, author, detail_url
):
    """Проверка, залогиненный пользователь может создать комментарий."""
    response = author_client.post(detail_url, data=form_data)
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == f"{detail_url}#comments"
    comments_count = Comment.objects.count()
    assert comments_count == 1
    comment = Comment.objects.get()
    assert comment.text == form_data['text']
    assert comment.news == news
    assert comment.author == author


@pytest.mark.django_db
def test_user_cant_use_bad_words(author_client, news, detail_url):
    """Проверка, пользователь не может использовать запрещенные слова."""
    bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
    response = author_client.post(detail_url, data=bad_words_data)
    assertFormError(response, 'form', 'text', WARNING)
    comments_count = Comment.objects.count()
    assert comments_count == 0


@pytest.mark.django_db
def test_user_cant_delete_comment_of_another_user(
    reader_client, comment, delete_url
):
    """Проверка, пользователь не может удалить комментарий другого юзера."""
    response = reader_client.delete(delete_url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comments_count = Comment.objects.count()
    assert comments_count == 1


@pytest.mark.django_db
def test_author_can_edit_comment(
    author_client, comment, form_data, detail_url, edit_url
):
    """Проверка, автор может редактировать свой комментарий."""
    url_to_comments = f"{detail_url}#comments"
    response = author_client.post(edit_url, data=form_data)
    assertRedirects(response, url_to_comments)
    comment.refresh_from_db()
    assert comment.text == form_data['text']


@pytest.mark.django_db
def test_author_can_delete_comment(
    author_client, comment, news, author, detail_url, delete_url
):
    """Проверка, автор может удалить свой комментарий."""
    url_to_comments = f"{detail_url}#comments"
    response = author_client.delete(delete_url)
    assertRedirects(response, url_to_comments)
    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_user_cant_edit_comment_of_anothers(
    reader_client, comment, form_data, edit_url
):
    """Проверка юзер не может редачить комментарии других"""
    original_comment = Comment.objects.get()
    response = reader_client.post(edit_url, data=form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    updated_comment = Comment.objects.get()
    assert updated_comment.news == original_comment.news
    assert updated_comment.author == original_comment.author
    assert updated_comment.text == original_comment.text
