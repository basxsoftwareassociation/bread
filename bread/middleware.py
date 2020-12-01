from django.http import HttpResponseRedirect
from django.urls import reverse


def RequireAuthenticationMiddleware(get_response):
    def middleware(request):

        if not request.user.is_authenticated and request.path != reverse("login"):
            return HttpResponseRedirect(reverse("login") + "?next=" + request.path)
        return get_response(request)

    return middleware
