import django
import pytest
import os

os.environ["DJANGO_SETTINGS_MODULE"] = "tests.django_settings"
django.setup()


@pytest.mark.django_db
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
    b.configure_user(r, u)

    u2 = User.objects.get_by_natural_key("test")

    assert u2.is_staff
    assert u2.is_superuser

    r.META["HTTP_X_USER_ROLE"] = "user"

    u = User(username="test2", password="test")
    b.configure_user(r, u)

    u2 = User.objects.get_by_natural_key("test2")

    assert not u2.is_staff
    assert not u2.is_superuser