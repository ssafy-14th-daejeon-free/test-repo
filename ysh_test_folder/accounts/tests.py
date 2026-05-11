from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

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

# Create your tests here.
