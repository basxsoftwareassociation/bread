import base64

from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User


class BasicHTTPAuthentication(BaseBackend):
    """
    Tries to authenticate a user via basic HTTP Authentication
    """

    def authenticate(self, request, **kwargs):
        if request is None:
            return None
        auth_header = request.headers.get("Authorization")
        if auth_header is None or not auth_header.startswith("Basic "):
            return None
        credentials_encoded = auth_header.split("Basic ", 1)[1]
        credentials = base64.b64decode(credentials_encoded).decode()
        username, password = credentials.split(":", 1)
        user = User.objects.filter(username=username).first()
        if user and check_password(password, user.password) and user.is_active:
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
