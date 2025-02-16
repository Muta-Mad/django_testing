"""Тесты контента."""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from notes.models import Note
from notes.forms import NoteForm

User = get_user_model()


class TestNoteVisibility(TestCase):
    """Тесты видимости заметок для автора и читателя."""

    @classmethod
    def setUpTestData(cls):
        """Создание тестовых данных: автора, читателя и заметки."""
        cls.author = User.objects.create(username='Лев Толстой')
        cls.reader = User.objects.create(username='Читатель простой')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author,
            slug='slug'
        )

        cls.author_client = Client()
        cls.reader_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader_client.force_login(cls.reader)

    def test_note_visibility_in_list(self):
        """Проверка видимости заметки в списке для разных пользователей."""
        test_cases = (
            (self.author_client, True),
            (self.reader_client, False),
        )

        for client, expected in test_cases:
            with self.subTest(client=client):
                url = reverse('notes:list')
                response = client.get(url)
                object_list = response.context['object_list']
                self.assertIs(
                    self.note in object_list,
                    expected)

    def test_pages_contains_form(self):
        """Проверка формы на страницах создания и редактирования заметки."""
        test_cases = [
            ('notes:add', None),
            ('notes:edit', (self.note.slug,))
        ]
        for name, args in test_cases:
            with self.subTest(name=name, args=args):
                url = reverse(name, args=args)
                response = self.author_client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)
