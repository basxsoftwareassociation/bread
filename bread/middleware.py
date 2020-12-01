from django.http import HttpResponseRedirect
from django.urls import reverse


def RequireAuthenticationMiddleware(get_response):
    def middleware(request):
        """All urls in the bread namespace require authentication"""

        if not request.user.is_authenticated:
            return HttpResponseRedirect(reverse("login") + "?next=" + request.path)
        return get_response(request)

    return middleware
