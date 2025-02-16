from http import HTTPStatus

import pytest

from django.urls import reverse

from news.forms import BAD_WORDS, WARNING
from news.models import Comment, News

COMMENT_TEXT = 'Текст комментария'
COMMENT_TEXT_NEW = 'Новый комментарий'

"""Создание данных для тестов(ФИКСТУР)"""


@pytest.fixture
def form_data():
    return {'text': COMMENT_TEXT_NEW}


@pytest.fixture
def author(django_user_model):
    return django_user_model.objects.create(username='Автор')


@pytest.fixture
def reader(django_user_model):
    return django_user_model.objects.create(username='Читатель')


@pytest.fixture
def news(author):
    return News.objects.create(
        title='Тестовая новость',
        text='Текст новости',
    )


@pytest.fixture
def comment(author, news):
    return Comment.objects.create(
        news=news,
        author=author,
        text=COMMENT_TEXT,
    )


@pytest.fixture
def author_client(author, client):
    client.force_login(author)
    return client


@pytest.fixture
def reader_client(reader, client):
    client.force_login(reader)
    return client


"""Тесты логики приложения"""


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(client, form_data, news):
    """Проверка, анонимный пользователь не может создать комментарий."""
    url = reverse('news:detail', args=(news.id,))
    client.post(url, data=form_data)
    comments_count = Comment.objects.count()
    assert comments_count == 0


@pytest.mark.django_db
def test_user_can_create_comment(author_client, form_data, news, author):
    """Проверка, залогиненный пользователь может создать комментарий."""
    url = reverse('news:detail', args=(news.id,))
    response = author_client.post(url, data=form_data)
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == f"{url}#comments"
    comments_count = Comment.objects.count()
    assert comments_count == 1
    comment = Comment.objects.get()
    assert comment.text == form_data['text']
    assert comment.news == news
    assert comment.author == author


@pytest.mark.django_db
def test_user_cant_use_bad_words(author_client, news):
    """Проверка, пользователь не может использовать запрещенные слова"""
    url = reverse('news:detail', args=(news.id,))
    bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
    response = author_client.post(url, data=bad_words_data)
    assert 'form' in response.context
    form = response.context['form']
    assert 'text' in form.errors
    assert WARNING in form.errors['text']
    comments_count = Comment.objects.count()
    assert comments_count == 0


@pytest.mark.django_db
def test_user_cant_delete_comment_of_another_user(reader_client, comment):
    """Проверка, пользователь не может удалить комментарий другого юзера."""
    comment_url = reverse('news:delete', args=(comment.id,))
    response = reader_client.delete(comment_url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comments_count = Comment.objects.count()
    assert comments_count == 1


@pytest.mark.django_db
def test_author_can_edit_comment(author_client, comment, form_data):
    """Проверка, автор может редактировать свой комментарий."""
    edit_url = reverse('news:edit', args=(comment.id,))
    news_url = reverse('news:detail', args=(comment.news.id,))
    url_to_comments = f"{news_url}#comments"
    response = author_client.post(edit_url, data=form_data)
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == url_to_comments
    comment.refresh_from_db()
    assert comment.text == COMMENT_TEXT_NEW


@pytest.mark.django_db
def test_author_can_delete_comment(author_client, comment, news, author):
    """Проверка, автор может удалить свой комментарий."""
    delete_url = reverse('news:delete', args=(comment.id,))
    news_url = reverse('news:detail', args=(news.id,))
    url_to_comments = f"{news_url}#comments"
    response = author_client.delete(delete_url)
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == url_to_comments
    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_user_cant_edit_comment_of_anothers(reader_client, comment, form_data):
    """Проверка юзер не может редачить комментарии других"""
    comment_url = reverse('news:edit', args=(comment.id,))
    response = reader_client.post(comment_url, data=form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment.refresh_from_db()
    assert comment.text == COMMENT_TEXT
