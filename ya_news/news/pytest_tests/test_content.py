from datetime import timedelta as td

from django.conf import settings
from django.urls import reverse
from django.utils import timezone as tz

import pytest

from news.models import News, Comment
from news.forms import CommentForm


@pytest.fixture
def author(django_user_model):
    return django_user_model.objects.create(username='Автор')


@pytest.fixture
def author_client(author, client):
    client.force_login(author)
    return client


@pytest.fixture
def news(author):
    return News.objects.create(
        title='Тестовая новость',
        text='Текст новости',
    )


@pytest.fixture
def create_news(author):
    today = tz.now()
    News.objects.bulk_create([
        News(
            title=f'Заголовок {index}',
            text=f'Текст {index}',
            date=today - td(days=index)
        )
        for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
    ])


@pytest.fixture
def comment(author, news):
    return Comment.objects.create(
        news=news,
        author=author,
        text='Текст комментария'
    )


@pytest.fixture
def create_comments(author, news):
    now = tz.now()
    for index in range(5):
        Comment.objects.create(
            news=news,
            author=author,
            text=f'Текст {index}',
            created=now + td(days=index)
        )


@pytest.mark.django_db
def test_news_count(client, create_news):
    """Проверка, на главной странице отображается
    правильное количество новостей.
    """
    url = reverse('news:home')
    response = client.get(url)
    object_list = response.context['object_list']
    assert len(object_list) == settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_news_order(client, create_news):
    """Проверка, новости отображаются по дате."""
    url = reverse('news:home')
    response = client.get(url)
    object_list = response.context['object_list']
    dates = [news.date for news in object_list]
    assert dates == sorted(dates, reverse=True)


@pytest.mark.django_db
def test_comments_order(client, news, create_comments):
    """Проверка, комментарии к новостям отображаются по дате создания."""
    url = reverse('news:detail', args=(news.id,))
    response = client.get(url)
    news = response.context['news']
    comments = news.comment_set.all()
    dates = [comment.created for comment in comments]
    assert dates == sorted(dates)


@pytest.mark.django_db
def test_anonymous_has_no_form(client, news):
    """Проверка, у анонимного пользователя нет формы
    для комментариев на странице новостей.
    """
    url = reverse('news:detail', args=(news.id,))
    response = client.get(url)
    assert 'form' not in response.context


@pytest.mark.django_db
def test_authorized_has_form(author_client, news):
    """Проверка, у авторизованного пользователя есть форма
    для комментариев на странице новостей.
    """
    url = reverse('news:detail', args=(news.id,))
    response = author_client.get(url)
    assert 'form' in response.context
    assert isinstance(response.context['form'], CommentForm)
