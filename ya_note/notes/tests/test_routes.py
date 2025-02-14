"""Тесты маршрутов."""
from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse

from notes.models import Note
from django.contrib.auth import get_user_model

User = get_user_model()


class TestRoutes(TestCase):
    """Тесты для проверки доступности маршрутов (URL) в приложении."""

    @classmethod
    def setUpTestData(cls):
        """Создание данных: автора и читателя для тестов."""
        cls.author = User.objects.create(username='Лев Толстой')
        cls.reader = User.objects.create(username='Читатель простой')
        cls.note = Note.objects.create(
            title='Заголовок', text='Текст', author=cls.author)

    def test_pages_availability(self):
        """Проверка доступа страниц для всех пользователей."""
        urls = (
            ('notes:home', None),
            ('users:login', None),
            ('users:logout', None),
            ('users:signup', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_authenticated_pages_availability(self):
        """Проверка доступа страниц для авторизованных пользователей."""
        self.client.force_login(self.author)
        urls = (
            ('notes:list', None),
            ('notes:add', None),
            ('notes:success', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_note_detail_availability(self):
        """Проверка доступа страницы заметки для автора и читателя."""
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            with self.subTest(user=user):
                url = reverse('notes:detail', args=(self.note.slug,))
                response = self.client.get(url)
                self.assertEqual(response.status_code, status)

    def test_availability_for_note_edit_and_delete(self):
        """Проверка доступна страниц редактирования и удаления заметки."""
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for name in ('notes:edit', 'notes:delete'):
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        """Проверка перенаправления анонимных пользователей."""
        login_url = reverse('users:login')
        urls = (
            ('notes:list', None),
            ('notes:add', None),
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
            ('notes:success', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
