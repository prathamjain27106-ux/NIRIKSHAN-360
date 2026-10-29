"""
Accounts tests — Phase 1 smoke tests.
"""

from django.test import TestCase
from .models import User


class UserModelTest(TestCase):
    def test_create_user_with_role(self):
        """Users are created with the correct role and string representation."""
        user = User.objects.create_user(
            username="analyst1",
            password="testpass123",
            role=User.Role.ANALYST,
            cell="PGRC",
        )
        self.assertEqual(user.role, "ANALYST")
        self.assertEqual(user.cell, "PGRC")
        self.assertIn("Complaint Analyst", str(user))

    def test_default_role_is_analyst(self):
        """Default role is ANALYST when none specified."""
        user = User.objects.create_user(username="default_user", password="testpass123")
        self.assertEqual(user.role, User.Role.ANALYST)
