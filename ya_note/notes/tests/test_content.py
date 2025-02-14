"""Тесты контента."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from notes.models import Note
from notes.forms import NoteForm

User = get_user_model()


class TestNoteVisibility(TestCase):
    """Тесты видимости заметок для автора и читателя."""

    @classmethod
    def setUpTestData(cls):
        """Создание тестовых данных: автора читателя, и заметки."""
        cls.author = User.objects.create(username='Лев Толстой')
        cls.reader = User.objects.create(username='Читатель простой')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author,
            slug='slug'
        )

    def test_note_in_list_for_author(self):
        """Проверка, автор видит свою заметку в списке заметок."""
        self.client.force_login(self.author)
        url = reverse('notes:list')
        response = self.client.get(url)
        object_list = response.context['object_list']
        self.assertIn(self.note, object_list)

    def test_note_not_in_list_for_reader(self):
        """Проверка, читатель не видит заметку, написанную автором."""
        self.client.force_login(self.reader)
        url = reverse('notes:list')
        response = self.client.get(url)
        object_list = response.context['object_list']
        self.assertNotIn(self.note, object_list)

    def test_pages_contains_form(self):
        """Проверка формы на страницах создания и редактирования заметки."""
        test_cases = [
            ('notes:add', None),
            ('notes:edit', [self.note.slug])
        ]
        for name, args in test_cases:
            with self.subTest(name=name, args=args):
                self.client.force_login(self.author)
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)
