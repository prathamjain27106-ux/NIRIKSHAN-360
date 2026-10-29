"""
Accounts views — current user profile endpoint.
"""

from rest_framework import generics, permissions
from .models import User
from .serializers import UserSerializer


class CurrentUserView(generics.RetrieveAPIView):
    """Return the authenticated user's profile."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
