import urllib

from django.http import HttpResponseRedirect
from django.urls import reverse


class RequireAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if "bread-cookies" not in request.session:
            request.session["bread-cookies"] = {}
        for k, v in request.COOKIES.items():
            if k.startswith("bread-"):
                request.session["bread-cookies"][k] = urllib.parse.unquote(v)
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        whitelisted_urlnames = (
            "login",
            "password_reset",
            "password_reset_done",
            "password_reset_confirm",
            "password_reset_complete",
        )
        if not (
            request.user.is_authenticated
            or request.resolver_match.url_name in whitelisted_urlnames
        ):
            return HttpResponseRedirect(reverse("login") + "?next=" + request.path)
        return None
