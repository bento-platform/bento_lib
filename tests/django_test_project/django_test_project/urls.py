from django.urls import include, path

urlpatterns = [
    path("", include("tests.django_test_project.test_app.urls")),
]
