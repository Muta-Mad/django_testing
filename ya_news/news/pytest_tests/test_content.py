from django.conf import settings
import pytest

from news.forms import CommentForm


@pytest.mark.django_db
def test_news_count(client, create_news, home_url):
    """Проверка, на главной странице отображается
    правильное количество новостей.
    """
    response = client.get(home_url)
    assert 'object_list' in response.context
    object_list = response.context['object_list']
    assert object_list.count() == settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_news_order(client, create_news, home_url):
    """Проверка, новости отображаются по дате."""
    response = client.get(home_url)
    assert 'object_list' in response.context
    object_list = response.context['object_list']
    dates = [news.date for news in object_list]
    assert dates == sorted(dates, reverse=True)


@pytest.mark.django_db
def test_comments_order(client, news, create_comments, detail_url):
    """Проверка, комментарии к новостям отображаются по дате создания."""
    response = client.get(detail_url)
    assert 'news' in response.context
    news = response.context['news']
    comments = news.comment_set.all()
    dates = [comment.created for comment in comments]
    assert dates == sorted(dates)


@pytest.mark.django_db
def test_anonymous_has_no_form(client, news, detail_url):
    """Проверка, у анонимного пользователя нет формы
    для комментариев на странице новостей.
    """
    response = client.get(detail_url)
    assert 'form' not in response.context


@pytest.mark.django_db
def test_authorized_has_form(author_client, news, detail_url):
    """Проверка, у авторизованного пользователя есть форма
    для комментариев на странице новостей.
    """
    response = author_client.get(detail_url)
    assert 'form' in response.context
    assert isinstance(response.context['form'], CommentForm)
