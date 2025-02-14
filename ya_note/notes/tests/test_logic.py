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
        cls.user = User.objects.create(username='Лев Толстой')
        cls.other_user = User.objects.create(username='Федор Достоевский')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.url = reverse('notes:add')
        cls.form_data = {
            'title': 'Заголовок',
            'text': 'Текст заметки',
            'slug': 'test-slug',
        }
        cls.note = Note.objects.create(
            title='Старый заголовок',
            text='Старый текст',
            author=cls.user,
            slug='old-slug'
        )

    def test_anonymous_user_cant_create_note(self):
        """Проверка, что анонимный пользователь не может создать заметку."""
        initial_note_count = Note.objects.count()
        response = self.client.post(self.url, data=self.form_data)
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={self.url}'
        self.assertRedirects(response, expected_url)
        final_note_count = Note.objects.count()
        self.assertEqual(final_note_count, initial_note_count)

    def test_logged_in_user_can_create_note(self):
        """Проверка, залогиненный пользователь может создать заметку."""
        url = reverse('notes:add')
        response = self.auth_client.post(url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.get()
        self.assertEqual(new_note.title, self.note['title'])
        self.assertEqual(new_note.text, self.note['text'])
        self.assertEqual(new_note.slug, self.note['slug'])
        self.assertEqual(new_note.author, self.user)

    def test_duplicate_slug(self):
        """Проверка, нельзя создать заметку с дублирующимся slug."""
        self.auth_client.post(self.url, data=self.form_data)
        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertFormError(
            response, 'form', 'slug', [self.form_data['slug'] + WARNING]
        )
                             
    def test_slug_auto_generation(self):
        """Проверка, slug автоматически генерируется, если не указан."""
        form_data_without_slug = {
            'title': 'Новый заголовок',
            'text': 'Новый текст заметки',
        }
        response = self.auth_client.post(self.url, data=form_data_without_slug)
        self.assertRedirects(response, self.url)
        note_count = Note.objects.count()
        self.assertEqual(note_count, 1)
        note = Note.objects.get()
        expected_slug = slugify(form_data_without_slug['title'])
        self.assertEqual(note.slug, expected_slug)
    
    def test_author_can_edit_note(self):
        """Проверка, что автор может редактировать свою заметку."""
        self.client.force_login(self.user)
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.client.post(url, self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.text, self.form_data['text'])
        self.assertEqual(self.note.slug, self.form_data['slug'])

    def test_non_author_cannot_edit_note(self):
        """Проверка, что неавтор не может редактировать заметку."""
        self.client.force_login(self.other_user)
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.client.post(url, self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertNotEqual(self.note.title, self.form_data['title'])
