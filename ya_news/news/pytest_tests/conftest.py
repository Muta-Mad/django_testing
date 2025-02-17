from datetime import timedelta as td

from django.urls import reverse
from django.utils import timezone as tz
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client
import pytest

from news.models import News, Comment

User = get_user_model()


@pytest.fixture
def author():
    return User.objects.create(username='Автор')


@pytest.fixture
def reader():
    return User.objects.create(username='Читатель')


@pytest.fixture
def author_client(author, client):
    client.force_login(author)
    return client


@pytest.fixture
def reader_client(reader):
    client = Client()
    client.force_login(reader)
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


@pytest.fixture
def form_data():
    return {'text': 'Новый комментарий'}


"""Фикстуры URL"""


@pytest.fixture
def home_url():
    return reverse('news:home')


@pytest.fixture
def detail_url(news):
    return reverse('news:detail', args=(news.id,))


@pytest.fixture
def delete_url(comment):
    return reverse('news:delete', args=(comment.id,))


@pytest.fixture
def edit_url(comment):
    return reverse('news:edit', args=(comment.id,))


@pytest.fixture
def login_url():
    return reverse('users:login')


@pytest.fixture
def logout_url():
    return reverse('users:logout')


@pytest.fixture
def signup_url():
    return reverse('users:signup')
