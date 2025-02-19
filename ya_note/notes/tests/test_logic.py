from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.models import Note
from notes.forms import WARNING


User = get_user_model()


class TestNoteCreation(TestCase):

    @classmethod
    def setUpTestData(cls):
        """Создание тестовых данных для создания заметки."""
        cls.url = reverse('notes:add')
        cls.user = User.objects.create(username='Лев Толстой')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.form_data = {
            'title': 'Заголовок',
            'text': 'Текст заметки',
            'slug': 'test-slug',
        }

    def test_anonymous_user_cant_create_note(self):
        """Проверка, что анонимный пользователь не может создать заметку."""
        response = self.client.post(self.url, data=self.form_data)
        note_count = Note.objects.count()
        self.assertEqual(note_count, 0)
        login_url = reverse('users:login')
        expected_redirect = f'{login_url}?next={self.url}'
        self.assertRedirects(response, expected_redirect)

    def test_logged_in_user_can_create_note(self):
        """Проверка, залогиненный пользователь может создать заметку."""
        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        note_count = Note.objects.count()
        self.assertEqual(note_count, 1)
        note = Note.objects.get()
        self.assertEqual(note.title, self.form_data['title'])
        self.assertEqual(note.text, self.form_data['text'])
        self.assertEqual(note.slug, self.form_data['slug'])
        self.assertEqual(note.author, self.user)

    def test_duplicate_slug(self):
        """Проверка, нельзя создать заметку с дублирующимся slug."""
        note = Note.objects.create(
            title='Заголовок заметки',
            text='Текст заметки',
            slug='test-slug',
            author=self.user,
        )
        self.assertEqual(Note.objects.count(), 1)
        self.form_data['slug'] = note.slug
        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertFormError(
            response, 'form', 'slug', [self.form_data['slug'] + WARNING])
        self.assertEqual(Note.objects.count(), 1)

    def test_slug_auto_generation(self):
        self.form_data.pop('slug')
        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        note_count = Note.objects.count()
        self.assertEqual(note_count, 1)
        created_note = Note.objects.get()
        excepted_slug = slugify(self.form_data['title'])
        self.assertEqual(created_note.slug, excepted_slug)


class TestNoteEditDelete(TestCase):

    @classmethod
    def setUpTestData(cls):
        """Создание тестовых данных для редактирования и удаления заметки."""
        cls.author = User.objects.create(username='Автор заметки')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.other_user = User.objects.create(username='Другой пользователь')
        cls.other_user_client = Client()
        cls.other_user_client.force_login(cls.other_user)
        cls.note = Note.objects.create(
            title='Заголовок заметки',
            text='Текст заметки',
            slug='test-slug',
            author=cls.author,
        )
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.form_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст заметки',
            'slug': 'new-slug'
        }

    def test_author_can_edit_note(self):
        """Проверка, автор может редактировать свою заметку."""
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.text, self.form_data['text'])
        self.assertEqual(self.note.slug, self.form_data['slug'])

    def test_author_can_delete_note(self):
        """Проверка, автор может удалить свою заметку."""
        response = self.author_client.post(self.delete_url)
        self.assertRedirects(response, reverse('notes:success'))
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_other_user_cant_edit_note(self):
        """Проверка, другой пользователь не может
        редактировать чужую заметку.
        """
        original_note = Note.objects.get()
        response = self.other_user_client.post(
            self.edit_url, data=self.form_data
        )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        updated_note = Note.objects.get(id=original_note.id)
        self.assertEqual(updated_note.title, original_note.title)
        self.assertEqual(updated_note.text, original_note.text)
        self.assertEqual(updated_note.slug, original_note.slug)
        self.assertEqual(updated_note.author, original_note.author)

    def test_other_user_cant_delete_note(self):
        """Проверка, что другой пользователь не может удалить чужую заметку."""
        response = self.other_user_client.post(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
