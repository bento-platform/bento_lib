from django.urls import path

from . import views

urlpatterns = [
    path("private/get", views.private_get, name="private-get"),
    path("private/get-missing", views.private_get_missing_flag, name="private-get-missing-flag"),
]
