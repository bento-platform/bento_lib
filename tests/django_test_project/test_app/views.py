from django.http import HttpResponse

from ..django_test_project.authz import authz


def private_get(request):
    authz.mark_authz_done(request)
    return HttpResponse("done")


def private_get_missing_flag(_request):
    # Missing flag - should give 403
    return HttpResponse("done")
