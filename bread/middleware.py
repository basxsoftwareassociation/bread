from django.http import HttpResponseRedirect
from django.urls import Resolver404, resolve, reverse


def RequireAuthenticationMiddleware(get_response):
    def middleware(request):

        whitelisted_urlnames = (
            "login",
            "password_reset",
            "password_reset_done",
            "password_reset_confirm",
            "password_reset_complete",
        )
        resolver_match = None
        try:
            resolver_match = resolve(request.path)
        except Resolver404:
            pass

        if request.user.is_authenticated or (
            resolver_match and resolver_match.url_name in whitelisted_urlnames
        ):
            return get_response(request)
        return HttpResponseRedirect(reverse("login") + "?next=" + request.path)

    return middleware
