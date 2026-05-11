from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from blog.models import Follow, Notification

from .models import Profile


class SignupTests(TestCase):
    def test_signup_creates_user_profile_and_logs_in(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "writer",
                "email": "writer@example.com",
                "display_name": "Writer",
                "bio": "Django blogger",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        user = User.objects.get(username="writer")
        self.assertRedirects(response, reverse("profile", args=[user.username]))
        self.assertEqual(user.email, "writer@example.com")
        self.assertEqual(Profile.objects.get(user=user).display_name, "Writer")
        self.assertIn("_auth_user_id", self.client.session)

    @override_settings(ENABLE_LOCAL_LOGIN=True)
    def test_local_login_creates_folder_local_account(self):
        response = self.client.post(reverse("local_login"), HTTP_HOST="localhost")

        user = User.objects.get(username="localtester")
        self.assertRedirects(response, reverse("post_list"))
        self.assertEqual(Profile.objects.get(user=user).display_name, "Local Tester")
        self.assertIn("_auth_user_id", self.client.session)

    @override_settings(ENABLE_LOCAL_LOGIN=False)
    def test_local_login_is_disabled_unless_explicitly_enabled(self):
        response = self.client.post(reverse("local_login"))

        self.assertEqual(response.status_code, 404)

    def test_follow_toggle_creates_notification(self):
        follower = User.objects.create_user("follower", password="StrongPass123!")
        target = User.objects.create_user("target", password="StrongPass123!")
        self.client.login(username="follower", password="StrongPass123!")

        response = self.client.post(reverse("toggle_follow", args=[target.username]))

        self.assertRedirects(response, reverse("profile", args=[target.username]))
        self.assertTrue(Follow.objects.filter(follower=follower, following=target).exists())
        self.assertTrue(
            Notification.objects.filter(
                recipient=target,
                actor=follower,
                kind=Notification.Kind.FOLLOW,
            ).exists()
        )

    def test_notifications_page_marks_items_read(self):
        recipient = User.objects.create_user("recipient", password="StrongPass123!")
        actor = User.objects.create_user("actor", password="StrongPass123!")
        notification = Notification.objects.create(
            recipient=recipient,
            actor=actor,
            kind=Notification.Kind.FOLLOW,
            message="actor followed you.",
        )
        self.client.login(username="recipient", password="StrongPass123!")

        response = self.client.get(reverse("notifications"))

        self.assertContains(response, "actor followed you.")
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

# Create your tests here.
