from asgiref.sync import iscoroutinefunction, markcoroutinefunction
from django.http import HttpRequest
from .middleware.base import BaseAuthMiddleware


def extract_middleware_arguments():
    # TODO
    return ()


class AsyncDjangoMiddleware(BaseAuthMiddleware):
    def __init__(self, get_response):
        # TODO: extract settings from Django settings

        self.get_response = get_response
        if iscoroutinefunction(self.get_response):
            markcoroutinefunction(self)

        super().__init__(*extract_middleware_arguments())

    async def __call__(self, request: HttpRequest):
        # TODO: impl
        pass


class SyncDjangoMiddleware(BaseAuthMiddleware):
    def __init__(self):
        # TODO: extract settings from Django settings
        super().__init__(*extract_middleware_arguments())

    def __call__(self, request: HttpRequest):
        # TODO: impl
        pass
