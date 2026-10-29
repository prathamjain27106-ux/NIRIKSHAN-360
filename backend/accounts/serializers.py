"""
Accounts serializers — User profile and registration.
"""

from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Read-only user profile serializer."""

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "role", "cell", "is_active", "created_at")
        read_only_fields = fields
