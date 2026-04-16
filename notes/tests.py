import time

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from .models import Note


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

class NoteCreateTests(TestCase):
    """Tests for creating notes."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            'testuser', 'test@example.com', 'testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_create_note(self):
        """Authenticated user can create a note."""
        resp = self.client.post('/api/notes/', {
            'title': 'My Note',
            'content': 'Hello world',
        })
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['title'], 'My Note')
        self.assertEqual(resp.data['content'], 'Hello world')

    def test_create_note_response_fields(self):
        """Created note response includes id and timestamps."""
        resp = self.client.post('/api/notes/', {
            'title': 'Fields Test',
            'content': 'Check fields',
        })
        self.assertIn('id', resp.data)
        self.assertIn('created_at', resp.data)
        self.assertIn('updated_at', resp.data)

    def test_create_note_assigned_to_user(self):
        """Created note belongs to the authenticated user."""
        resp = self.client.post('/api/notes/', {
            'title': 'Ownership',
            'content': 'Mine',
        })
        note = Note.objects.get(id=resp.data['id'])
        self.assertEqual(note.user, self.user)

    def test_create_note_without_title(self):
        """Note can be created with empty title."""
        resp = self.client.post('/api/notes/', {
            'content': 'No title here',
        })
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['title'], '')

    def test_create_note_without_content(self):
        """Note can be created with empty content."""
        resp = self.client.post('/api/notes/', {
            'title': 'Title only',
        })
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['content'], '')

    def test_create_empty_note(self):
        """Note can be created with no title and no content."""
        resp = self.client.post('/api/notes/', {})
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['title'], '')
        self.assertEqual(resp.data['content'], '')

    def test_create_note_requires_auth(self):
        """Unauthenticated users cannot create notes."""
        client = APIClient()
        resp = client.post('/api/notes/', {'title': 'Test'})
        self.assertEqual(resp.status_code, 401)


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

class NoteListTests(TestCase):
    """Tests for listing notes."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            'testuser', 'test@example.com', 'testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_list_notes_empty(self):
        """Returns empty list when user has no notes."""
        resp = self.client.get('/api/notes/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, [])

    def test_list_own_notes(self):
        """User sees only their own notes."""
        Note.objects.create(user=self.user, title='My Note')
        other_user = User.objects.create_user('other', 'o@b.com', 'pass12345')
        Note.objects.create(user=other_user, title='Other Note')

        resp = self.client.get('/api/notes/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['title'], 'My Note')

    def test_list_multiple_notes(self):
        """All of the user's notes are returned."""
        Note.objects.create(user=self.user, title='Note 1')
        Note.objects.create(user=self.user, title='Note 2')
        Note.objects.create(user=self.user, title='Note 3')

        resp = self.client.get('/api/notes/')
        self.assertEqual(len(resp.data), 3)

    def test_list_notes_ordered_by_updated(self):
        """Notes are returned most-recently-updated first."""
        note_a = Note.objects.create(user=self.user, title='First')
        note_b = Note.objects.create(user=self.user, title='Second')
        # Update note_a so it becomes the most recently updated
        note_a.title = 'First Updated'
        note_a.save()

        resp = self.client.get('/api/notes/')
        self.assertEqual(resp.data[0]['title'], 'First Updated')
        self.assertEqual(resp.data[1]['title'], 'Second')

    def test_list_notes_response_shape(self):
        """Each note in the list has all expected fields."""
        Note.objects.create(user=self.user, title='Shape', content='Check')
        resp = self.client.get('/api/notes/')
        note = resp.data[0]
        self.assertIn('id', note)
        self.assertIn('title', note)
        self.assertIn('content', note)
        self.assertIn('created_at', note)
        self.assertIn('updated_at', note)

    def test_list_notes_requires_auth(self):
        """Unauthenticated users cannot list notes."""
        client = APIClient()
        resp = client.get('/api/notes/')
        self.assertEqual(resp.status_code, 401)


# ---------------------------------------------------------------------------
# Detail (GET single)
# ---------------------------------------------------------------------------

class NoteDetailTests(TestCase):
    """Tests for retrieving a single note."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            'testuser', 'test@example.com', 'testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.note = Note.objects.create(
            user=self.user, title='Test Note', content='Content'
        )

    def test_get_own_note(self):
        """User can retrieve their own note."""
        resp = self.client.get(f'/api/notes/{self.note.id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['title'], 'Test Note')
        self.assertEqual(resp.data['content'], 'Content')

    def test_get_note_response_fields(self):
        """Detail response includes all expected fields."""
        resp = self.client.get(f'/api/notes/{self.note.id}/')
        self.assertIn('id', resp.data)
        self.assertIn('title', resp.data)
        self.assertIn('content', resp.data)
        self.assertIn('created_at', resp.data)
        self.assertIn('updated_at', resp.data)

    def test_cannot_get_other_users_note(self):
        """User cannot access another user's note."""
        other_user = User.objects.create_user('other', 'o@b.com', 'pass12345')
        other_note = Note.objects.create(user=other_user, title='Secret')
        resp = self.client.get(f'/api/notes/{other_note.id}/')
        self.assertEqual(resp.status_code, 404)

    def test_get_nonexistent_note(self):
        """Returns 404 for non-existent note ID."""
        resp = self.client.get('/api/notes/99999/')
        self.assertEqual(resp.status_code, 404)

    def test_get_note_requires_auth(self):
        """Detail endpoint requires authentication."""
        client = APIClient()
        resp = client.get(f'/api/notes/{self.note.id}/')
        self.assertEqual(resp.status_code, 401)


# ---------------------------------------------------------------------------
# Update (PATCH)
# ---------------------------------------------------------------------------

class NoteUpdateTests(TestCase):
    """Tests for updating notes."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            'testuser', 'test@example.com', 'testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.note = Note.objects.create(
            user=self.user, title='Original', content='Original content'
        )

    def test_update_note_title(self):
        """User can update a note's title."""
        resp = self.client.patch(f'/api/notes/{self.note.id}/', {
            'title': 'Updated Title',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['title'], 'Updated Title')
        self.assertEqual(resp.data['content'], 'Original content')

    def test_update_note_content(self):
        """User can update a note's content."""
        resp = self.client.patch(f'/api/notes/{self.note.id}/', {
            'content': 'New content',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['content'], 'New content')
        self.assertEqual(resp.data['title'], 'Original')

    def test_update_both_fields(self):
        """User can update title and content at the same time."""
        resp = self.client.patch(f'/api/notes/{self.note.id}/', {
            'title': 'New Title',
            'content': 'New Content',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['title'], 'New Title')
        self.assertEqual(resp.data['content'], 'New Content')

    def test_update_persists_to_database(self):
        """Update is persisted to the database."""
        self.client.patch(f'/api/notes/{self.note.id}/', {
            'title': 'Persisted',
        })
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, 'Persisted')

    def test_cannot_update_other_users_note(self):
        """User cannot update another user's note."""
        other_user = User.objects.create_user('other', 'o@b.com', 'pass12345')
        other_note = Note.objects.create(user=other_user, title='Secret')
        resp = self.client.patch(f'/api/notes/{other_note.id}/', {
            'title': 'Hacked',
        })
        self.assertEqual(resp.status_code, 404)

    def test_update_nonexistent_note(self):
        """Returns 404 for updating a non-existent note."""
        resp = self.client.patch('/api/notes/99999/', {
            'title': 'Ghost',
        })
        self.assertEqual(resp.status_code, 404)

    def test_update_requires_auth(self):
        """Update endpoint requires authentication."""
        client = APIClient()
        resp = client.patch(f'/api/notes/{self.note.id}/', {
            'title': 'Nope',
        })
        self.assertEqual(resp.status_code, 401)


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

class NoteDeleteTests(TestCase):
    """Tests for deleting notes."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            'testuser', 'test@example.com', 'testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.note = Note.objects.create(
            user=self.user, title='To Delete', content='Goodbye'
        )

    def test_delete_own_note(self):
        """User can delete their own note."""
        resp = self.client.delete(f'/api/notes/{self.note.id}/')
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(Note.objects.filter(id=self.note.id).exists())

    def test_delete_removes_from_list(self):
        """Deleted note no longer appears in the list endpoint."""
        self.client.delete(f'/api/notes/{self.note.id}/')
        resp = self.client.get('/api/notes/')
        self.assertEqual(len(resp.data), 0)

    def test_cannot_delete_other_users_note(self):
        """User cannot delete another user's note."""
        other_user = User.objects.create_user('other', 'o@b.com', 'pass12345')
        other_note = Note.objects.create(user=other_user, title='Secret')
        resp = self.client.delete(f'/api/notes/{other_note.id}/')
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(Note.objects.filter(id=other_note.id).exists())

    def test_delete_nonexistent_note(self):
        """Returns 404 when deleting non-existent note."""
        resp = self.client.delete('/api/notes/99999/')
        self.assertEqual(resp.status_code, 404)

    def test_delete_requires_auth(self):
        """Delete endpoint requires authentication."""
        client = APIClient()
        resp = client.delete(f'/api/notes/{self.note.id}/')
        self.assertEqual(resp.status_code, 401)
        self.assertTrue(Note.objects.filter(id=self.note.id).exists())


# ---------------------------------------------------------------------------
# Note model
# ---------------------------------------------------------------------------

class NoteModelTests(TestCase):
    """Tests for the Note model itself."""

    def setUp(self):
        self.user = User.objects.create_user(
            'testuser', 'test@example.com', 'testpass123'
        )

    def test_str_with_title(self):
        """String representation uses the title when present."""
        note = Note.objects.create(user=self.user, title='My Title')
        self.assertEqual(str(note), 'My Title')

    def test_str_without_title(self):
        """String representation falls back to 'Note <pk>' when no title."""
        note = Note.objects.create(user=self.user, title='')
        self.assertEqual(str(note), f'Note {note.pk}')

    def test_default_ordering(self):
        """Notes are ordered by -updated_at by default."""
        note_a = Note.objects.create(user=self.user, title='A')
        note_b = Note.objects.create(user=self.user, title='B')
        # Update A so it's most recent
        note_a.content = 'updated'
        note_a.save()

        notes = list(Note.objects.filter(user=self.user))
        self.assertEqual(notes[0].id, note_a.id)
        self.assertEqual(notes[1].id, note_b.id)

    def test_cascade_delete_user(self):
        """Deleting a user cascades to delete all their notes."""
        Note.objects.create(user=self.user, title='Note 1')
        Note.objects.create(user=self.user, title='Note 2')
        user_id = self.user.id
        self.user.delete()
        self.assertEqual(Note.objects.filter(user_id=user_id).count(), 0)

    def test_cascade_does_not_affect_other_users(self):
        """Deleting one user's notes doesn't affect another user's notes."""
        other_user = User.objects.create_user('other', 'o@b.com', 'pass12345')
        Note.objects.create(user=self.user, title='Mine')
        Note.objects.create(user=other_user, title='Theirs')
        self.user.delete()
        self.assertEqual(Note.objects.filter(user=other_user).count(), 1)


# ---------------------------------------------------------------------------
# Full CRUD flow
# ---------------------------------------------------------------------------

class NoteCRUDFlowTests(TestCase):
    """End-to-end: create -> read -> update -> list -> delete."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            'testuser', 'test@example.com', 'testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_full_crud_flow(self):
        """Complete lifecycle of a note: create, read, update, delete."""
        # Create
        create_resp = self.client.post('/api/notes/', {
            'title': 'Flow Note',
            'content': 'Initial content',
        })
        self.assertEqual(create_resp.status_code, 201)
        note_id = create_resp.data['id']

        # Read
        get_resp = self.client.get(f'/api/notes/{note_id}/')
        self.assertEqual(get_resp.status_code, 200)
        self.assertEqual(get_resp.data['title'], 'Flow Note')

        # Update
        patch_resp = self.client.patch(f'/api/notes/{note_id}/', {
            'title': 'Updated Flow Note',
            'content': 'Updated content',
        })
        self.assertEqual(patch_resp.status_code, 200)
        self.assertEqual(patch_resp.data['title'], 'Updated Flow Note')

        # Verify in list
        list_resp = self.client.get('/api/notes/')
        self.assertEqual(len(list_resp.data), 1)
        self.assertEqual(list_resp.data[0]['title'], 'Updated Flow Note')

        # Delete
        del_resp = self.client.delete(f'/api/notes/{note_id}/')
        self.assertEqual(del_resp.status_code, 204)

        # Verify gone
        get_resp = self.client.get(f'/api/notes/{note_id}/')
        self.assertEqual(get_resp.status_code, 404)

        list_resp = self.client.get('/api/notes/')
        self.assertEqual(len(list_resp.data), 0)
