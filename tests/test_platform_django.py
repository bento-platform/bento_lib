import django
import os

os.environ["DJANGO_SETTINGS_MODULE"] = "tests.django_settings"
django.setup()


def test_remote_auth_backend():
    import chord_lib.auth.django_remote_user
    from django.contrib.auth.models import User
    from django.http.request import HttpRequest

    b = chord_lib.auth.django_remote_user.CHORDRemoteUserBackend()
    r = HttpRequest()
    r.META = {
        "HTTP_X_USER": "test",
        "HTTP_X_USER_ROLE": "owner"
    }

    u = User(username="test", password="test")
    u = b.configure_user(r, u)

    assert u.is_staff
    assert u.is_superuser

    r.META["HTTP_X_USER_ROLE"] = "user"

    u = User(username="test", password="test")
    u = b.configure_user(r, u)

    assert not u.is_staff
    assert not u.is_superuser
