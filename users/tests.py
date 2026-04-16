from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from .models import PasswordResetToken, UserProfile


# ---------------------------------------------------------------------------
# Signup
# ---------------------------------------------------------------------------

class SignupTests(TestCase):
    """Tests for user registration."""

    def setUp(self):
        self.client = APIClient()

    def test_signup_success(self):
        """New user can register with valid credentials."""
        resp = self.client.post('/api/auth/signup/', {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'testpass123',
        })
        self.assertEqual(resp.status_code, 201)
        self.assertIn('token', resp.data)
        self.assertEqual(resp.data['user']['username'], 'newuser')
        self.assertEqual(resp.data['user']['email'], 'new@example.com')
        self.assertIn('id', resp.data['user'])

    def test_signup_creates_profile(self):
        """Signing up automatically creates a UserProfile."""
        self.client.post('/api/auth/signup/', {
            'username': 'profileuser',
            'email': 'profile@example.com',
            'password': 'testpass123',
        })
        user = User.objects.get(username='profileuser')
        self.assertTrue(UserProfile.objects.filter(user=user).exists())

    def test_signup_token_works_for_auth(self):
        """Token returned from signup can access protected endpoints."""
        resp = self.client.post('/api/auth/signup/', {
            'username': 'authcheck',
            'email': 'auth@example.com',
            'password': 'testpass123',
        })
        token = resp.data['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        profile_resp = self.client.get('/api/auth/profile/')
        self.assertEqual(profile_resp.status_code, 200)
        self.assertEqual(profile_resp.data['username'], 'authcheck')

    def test_signup_duplicate_username(self):
        """Cannot register with an existing username."""
        User.objects.create_user('taken', 'a@b.com', 'pass12345')
        resp = self.client.post('/api/auth/signup/', {
            'username': 'taken',
            'email': 'other@example.com',
            'password': 'testpass123',
        })
        self.assertEqual(resp.status_code, 400)

    def test_signup_duplicate_email(self):
        """Cannot register with an existing email."""
        User.objects.create_user('user1', 'dup@example.com', 'pass12345')
        resp = self.client.post('/api/auth/signup/', {
            'username': 'user2',
            'email': 'dup@example.com',
            'password': 'testpass123',
        })
        self.assertEqual(resp.status_code, 400)

    def test_signup_short_password(self):
        """Password must be at least 8 characters."""
        resp = self.client.post('/api/auth/signup/', {
            'username': 'shortpw',
            'email': 'short@example.com',
            'password': 'abc',
        })
        self.assertEqual(resp.status_code, 400)

    def test_signup_missing_username(self):
        """Username is required."""
        resp = self.client.post('/api/auth/signup/', {
            'email': 'no_user@example.com',
            'password': 'testpass123',
        })
        self.assertEqual(resp.status_code, 400)

    def test_signup_missing_email(self):
        """Email is required."""
        resp = self.client.post('/api/auth/signup/', {
            'username': 'nomail',
            'password': 'testpass123',
        })
        self.assertEqual(resp.status_code, 400)

    def test_signup_missing_password(self):
        """Password is required."""
        resp = self.client.post('/api/auth/signup/', {
            'username': 'nopw',
            'email': 'nopw@example.com',
        })
        self.assertEqual(resp.status_code, 400)

    def test_signup_creates_user_in_database(self):
        """Signup actually persists the user to the database."""
        self.client.post('/api/auth/signup/', {
            'username': 'persist',
            'email': 'persist@example.com',
            'password': 'testpass123',
        })
        self.assertTrue(User.objects.filter(username='persist').exists())


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class LoginTests(TestCase):
    """Tests for user login."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            'testuser', 'test@example.com', 'testpass123'
        )

    def test_login_success(self):
        """User can log in with correct credentials."""
        resp = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn('token', resp.data)
        self.assertEqual(resp.data['user']['username'], 'testuser')
        self.assertEqual(resp.data['user']['email'], 'test@example.com')
        self.assertIn('id', resp.data['user'])

    def test_login_returns_same_token(self):
        """Logging in twice returns the same token (get_or_create)."""
        resp1 = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123',
        })
        resp2 = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123',
        })
        self.assertEqual(resp1.data['token'], resp2.data['token'])

    def test_login_token_works_for_auth(self):
        """Token returned from login can access protected endpoints."""
        resp = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123',
        })
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {resp.data["token"]}')
        profile_resp = self.client.get('/api/auth/profile/')
        self.assertEqual(profile_resp.status_code, 200)

    def test_login_wrong_password(self):
        """Login fails with wrong password."""
        resp = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'wrongpass',
        })
        self.assertEqual(resp.status_code, 401)

    def test_login_nonexistent_user(self):
        """Login fails for non-existent user."""
        resp = self.client.post('/api/auth/login/', {
            'username': 'nobody',
            'password': 'testpass123',
        })
        self.assertEqual(resp.status_code, 401)

    def test_login_missing_username(self):
        """Login requires username."""
        resp = self.client.post('/api/auth/login/', {
            'password': 'testpass123',
        })
        self.assertEqual(resp.status_code, 400)

    def test_login_missing_password(self):
        """Login requires password."""
        resp = self.client.post('/api/auth/login/', {
            'username': 'testuser',
        })
        self.assertEqual(resp.status_code, 400)


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

class LogoutTests(TestCase):
    """Tests for user logout."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            'testuser', 'test@example.com', 'testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_logout_deletes_token(self):
        """Logout deletes the auth token."""
        resp = self.client.post('/api/auth/logout/')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Token.objects.filter(user=self.user).exists())

    def test_logout_token_invalid_after(self):
        """Token cannot be used after logout."""
        self.client.post('/api/auth/logout/')
        resp = self.client.get('/api/auth/profile/')
        self.assertEqual(resp.status_code, 401)

    def test_logout_requires_auth(self):
        """Logout requires authentication."""
        client = APIClient()
        resp = client.post('/api/auth/logout/')
        self.assertEqual(resp.status_code, 401)


# ---------------------------------------------------------------------------
# Token authentication edge cases
# ---------------------------------------------------------------------------

class TokenAuthTests(TestCase):
    """Tests for token authentication edge cases."""

    def test_invalid_token_rejected(self):
        """Requests with an invalid token are rejected."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token invalidtokenstring123')
        resp = client.get('/api/auth/profile/')
        self.assertEqual(resp.status_code, 401)

    def test_no_token_rejected(self):
        """Requests without any token are rejected on protected endpoints."""
        client = APIClient()
        resp = client.get('/api/auth/profile/')
        self.assertEqual(resp.status_code, 401)

    def test_malformed_auth_header(self):
        """Requests with a malformed Authorization header are rejected."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer somejwttoken')
        resp = client.get('/api/auth/profile/')
        self.assertEqual(resp.status_code, 401)


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

class ProfileTests(TestCase):
    """Tests for user profile."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            'testuser', 'test@example.com', 'testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_get_profile(self):
        """Authenticated user can view their profile."""
        resp = self.client.get('/api/auth/profile/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['username'], 'testuser')
        self.assertEqual(resp.data['email'], 'test@example.com')

    def test_profile_contains_all_fields(self):
        """Profile response includes id, username, email, timestamps."""
        resp = self.client.get('/api/auth/profile/')
        self.assertIn('id', resp.data)
        self.assertIn('username', resp.data)
        self.assertIn('email', resp.data)
        self.assertIn('created_at', resp.data)
        self.assertIn('updated_at', resp.data)

    def test_profile_requires_auth(self):
        """Profile endpoint requires authentication."""
        client = APIClient()
        resp = client.get('/api/auth/profile/')
        self.assertEqual(resp.status_code, 401)


# ---------------------------------------------------------------------------
# Change password
# ---------------------------------------------------------------------------

class ChangePasswordTests(TestCase):
    """Tests for password change."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            'testuser', 'test@example.com', 'testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_change_password_success(self):
        """User can change their password with correct old password."""
        resp = self.client.post('/api/auth/change-password/', {
            'old_password': 'testpass123',
            'new_password': 'newpass12345',
        })
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass12345'))

    def test_can_login_with_new_password(self):
        """After changing password, user can log in with the new one."""
        self.client.post('/api/auth/change-password/', {
            'old_password': 'testpass123',
            'new_password': 'newpass12345',
        })
        client = APIClient()
        resp = client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'newpass12345',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn('token', resp.data)

    def test_old_password_fails_after_change(self):
        """After changing password, old password no longer works for login."""
        self.client.post('/api/auth/change-password/', {
            'old_password': 'testpass123',
            'new_password': 'newpass12345',
        })
        client = APIClient()
        resp = client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123',
        })
        self.assertEqual(resp.status_code, 401)

    def test_change_password_wrong_old(self):
        """Cannot change password with incorrect old password."""
        resp = self.client.post('/api/auth/change-password/', {
            'old_password': 'wrongoldpass',
            'new_password': 'newpass12345',
        })
        self.assertEqual(resp.status_code, 400)

    def test_change_password_too_short(self):
        """New password must be at least 8 characters."""
        resp = self.client.post('/api/auth/change-password/', {
            'old_password': 'testpass123',
            'new_password': 'short',
        })
        self.assertEqual(resp.status_code, 400)

    def test_change_password_missing_fields(self):
        """Both old and new password are required."""
        resp = self.client.post('/api/auth/change-password/', {
            'old_password': 'testpass123',
        })
        self.assertEqual(resp.status_code, 400)

    def test_change_password_requires_auth(self):
        """Change password requires authentication."""
        client = APIClient()
        resp = client.post('/api/auth/change-password/', {
            'old_password': 'testpass123',
            'new_password': 'newpass12345',
        })
        self.assertEqual(resp.status_code, 401)


# ---------------------------------------------------------------------------
# Request password reset
# ---------------------------------------------------------------------------

class RequestPasswordResetTests(TestCase):
    """Tests for requesting a password reset email."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            'testuser', 'test@example.com', 'testpass123'
        )

    def test_request_reset_valid_email(self):
        """Requesting a reset for a valid email returns 200."""
        resp = self.client.post('/api/auth/request-password-reset/', {
            'email': 'test@example.com',
        })
        self.assertEqual(resp.status_code, 200)

    def test_request_reset_creates_token(self):
        """Requesting a reset creates a PasswordResetToken for that user."""
        self.client.post('/api/auth/request-password-reset/', {
            'email': 'test@example.com',
        })
        self.assertTrue(
            PasswordResetToken.objects.filter(user=self.user).exists()
        )

    def test_request_reset_invalid_email_still_200(self):
        """Returns 200 even for non-existent email (no info leak)."""
        resp = self.client.post('/api/auth/request-password-reset/', {
            'email': 'nobody@example.com',
        })
        self.assertEqual(resp.status_code, 200)

    def test_request_reset_invalid_email_no_token(self):
        """No token is created for a non-existent email."""
        self.client.post('/api/auth/request-password-reset/', {
            'email': 'nobody@example.com',
        })
        self.assertEqual(PasswordResetToken.objects.count(), 0)

    def test_request_reset_multiple_tokens(self):
        """Multiple reset requests create multiple tokens."""
        self.client.post('/api/auth/request-password-reset/', {
            'email': 'test@example.com',
        })
        self.client.post('/api/auth/request-password-reset/', {
            'email': 'test@example.com',
        })
        self.assertEqual(
            PasswordResetToken.objects.filter(user=self.user).count(), 2
        )


# ---------------------------------------------------------------------------
# Reset password (with token)
# ---------------------------------------------------------------------------

class ResetPasswordTests(TestCase):
    """Tests for resetting a password with a token."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            'testuser', 'test@example.com', 'testpass123'
        )
        self.reset_token = PasswordResetToken.objects.create(
            user=self.user,
            token=PasswordResetToken.generate_token(),
        )

    def test_reset_password_success(self):
        """Password can be reset with a valid token."""
        resp = self.client.post('/api/auth/reset-password/', {
            'token': self.reset_token.token,
            'password': 'brandnewpass123',
        })
        self.assertEqual(resp.status_code, 200)

    def test_reset_password_updates_password(self):
        """After reset, the user's password is actually changed."""
        self.client.post('/api/auth/reset-password/', {
            'token': self.reset_token.token,
            'password': 'brandnewpass123',
        })
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('brandnewpass123'))

    def test_reset_password_marks_token_used(self):
        """After a successful reset, the token is marked as used."""
        self.client.post('/api/auth/reset-password/', {
            'token': self.reset_token.token,
            'password': 'brandnewpass123',
        })
        self.reset_token.refresh_from_db()
        self.assertTrue(self.reset_token.used)

    def test_reset_password_can_login_after(self):
        """After reset, user can log in with the new password."""
        self.client.post('/api/auth/reset-password/', {
            'token': self.reset_token.token,
            'password': 'brandnewpass123',
        })
        resp = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'brandnewpass123',
        })
        self.assertEqual(resp.status_code, 200)

    def test_reset_password_old_password_fails(self):
        """After reset, the old password no longer works."""
        self.client.post('/api/auth/reset-password/', {
            'token': self.reset_token.token,
            'password': 'brandnewpass123',
        })
        resp = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123',
        })
        self.assertEqual(resp.status_code, 401)

    def test_reset_password_used_token_rejected(self):
        """A token that has already been used cannot be reused."""
        self.reset_token.mark_as_used()
        resp = self.client.post('/api/auth/reset-password/', {
            'token': self.reset_token.token,
            'password': 'brandnewpass123',
        })
        self.assertEqual(resp.status_code, 400)

    def test_reset_password_invalid_token(self):
        """A completely invalid token string is rejected."""
        resp = self.client.post('/api/auth/reset-password/', {
            'token': 'totally-bogus-token-value',
            'password': 'brandnewpass123',
        })
        self.assertEqual(resp.status_code, 400)

    def test_reset_password_short_password(self):
        """New password must be at least 8 characters."""
        resp = self.client.post('/api/auth/reset-password/', {
            'token': self.reset_token.token,
            'password': 'short',
        })
        self.assertEqual(resp.status_code, 400)

    def test_reset_password_missing_token(self):
        """Token field is required."""
        resp = self.client.post('/api/auth/reset-password/', {
            'password': 'brandnewpass123',
        })
        self.assertEqual(resp.status_code, 400)

    def test_reset_password_missing_password(self):
        """Password field is required."""
        resp = self.client.post('/api/auth/reset-password/', {
            'token': self.reset_token.token,
        })
        self.assertEqual(resp.status_code, 400)

    def test_reset_password_expired_token(self):
        """A token older than 24 hours is rejected."""
        self.reset_token.created_at = timezone.now() - timedelta(hours=25)
        self.reset_token.save(update_fields=['created_at'])
        resp = self.client.post('/api/auth/reset-password/', {
            'token': self.reset_token.token,
            'password': 'brandnewpass123',
        })
        self.assertEqual(resp.status_code, 400)


# ---------------------------------------------------------------------------
# Full end-to-end password reset flow
# ---------------------------------------------------------------------------

class PasswordResetFlowTests(TestCase):
    """End-to-end: request reset -> use token -> login with new password."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            'testuser', 'test@example.com', 'testpass123'
        )

    def test_full_reset_flow(self):
        """Complete flow: request reset, grab token, reset, login."""
        # Step 1: Request reset
        self.client.post('/api/auth/request-password-reset/', {
            'email': 'test@example.com',
        })

        # Step 2: Grab the created token from the database
        reset_token = PasswordResetToken.objects.get(user=self.user)

        # Step 3: Reset password
        resp = self.client.post('/api/auth/reset-password/', {
            'token': reset_token.token,
            'password': 'mynewsecurepass',
        })
        self.assertEqual(resp.status_code, 200)

        # Step 4: Login with new password
        resp = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'mynewsecurepass',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn('token', resp.data)


# ---------------------------------------------------------------------------
# PasswordResetToken model
# ---------------------------------------------------------------------------

class PasswordResetTokenModelTests(TestCase):
    """Tests for the PasswordResetToken model."""

    def setUp(self):
        self.user = User.objects.create_user(
            'testuser', 'test@example.com', 'testpass123'
        )

    def test_generate_token(self):
        """Token generation produces a non-empty string."""
        token = PasswordResetToken.generate_token()
        self.assertTrue(len(token) > 0)

    def test_generate_token_is_unique(self):
        """Two generated tokens are different."""
        t1 = PasswordResetToken.generate_token()
        t2 = PasswordResetToken.generate_token()
        self.assertNotEqual(t1, t2)

    def test_token_is_valid_when_fresh(self):
        """A freshly created token is valid."""
        token = PasswordResetToken.objects.create(
            user=self.user,
            token=PasswordResetToken.generate_token(),
        )
        self.assertTrue(token.is_valid())

    def test_token_invalid_after_used(self):
        """A used token is no longer valid."""
        token = PasswordResetToken.objects.create(
            user=self.user,
            token=PasswordResetToken.generate_token(),
        )
        token.mark_as_used()
        self.assertFalse(token.is_valid())

    def test_token_invalid_after_24_hours(self):
        """A token older than 24 hours is no longer valid."""
        token = PasswordResetToken.objects.create(
            user=self.user,
            token=PasswordResetToken.generate_token(),
        )
        token.created_at = timezone.now() - timedelta(hours=25)
        token.save(update_fields=['created_at'])
        self.assertFalse(token.is_valid())

    def test_str(self):
        """String representation includes the username."""
        token = PasswordResetToken.objects.create(
            user=self.user,
            token=PasswordResetToken.generate_token(),
        )
        self.assertIn('testuser', str(token))


# ---------------------------------------------------------------------------
# UserProfile model
# ---------------------------------------------------------------------------

class UserProfileModelTests(TestCase):
    """Tests for the UserProfile model."""

    def test_profile_created_on_user_create(self):
        """Creating a user via create_user triggers the signal to make a profile."""
        user = User.objects.create_user('siguser', 'sig@example.com', 'pass12345')
        self.assertTrue(UserProfile.objects.filter(user=user).exists())

    def test_str(self):
        """String representation includes the username."""
        user = User.objects.create_user('struser', 'str@example.com', 'pass12345')
        self.assertIn('struser', str(user.profile))

    def test_cascade_delete(self):
        """Deleting a user also deletes their profile."""
        user = User.objects.create_user('deluser', 'del@example.com', 'pass12345')
        profile_id = user.profile.id
        user.delete()
        self.assertFalse(UserProfile.objects.filter(id=profile_id).exists())

    def test_cascade_delete_reset_tokens(self):
        """Deleting a user also deletes their password reset tokens."""
        user = User.objects.create_user('deluser2', 'del2@example.com', 'pass12345')
        PasswordResetToken.objects.create(
            user=user, token=PasswordResetToken.generate_token()
        )
        user.delete()
        self.assertEqual(PasswordResetToken.objects.count(), 0)
