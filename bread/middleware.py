import urllib

from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import LANGUAGE_SESSION_KEY, activate, get_language


class RequireAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if "bread-cookies" not in request.session:
            request.session["bread-cookies"] = {}
        for k, v in request.COOKIES.items():
            if k.startswith("bread-"):
                request.session["bread-cookies"][k] = urllib.parse.unquote(v)

        if request.user and hasattr(request.user, "preferences"):
            lang = request.user.preferences.get("general__preferred_language")
            if lang and lang != get_language():
                activate(lang)
                request.session[LANGUAGE_SESSION_KEY] = lang

        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        whitelisted_urlnames = (
            "login",
            "password_reset",
            "password_reset_done",
            "password_reset_confirm",
            "password_reset_complete",
        )
        if request.user.is_authenticated:
            return None
        if request.resolver_match.url_name in whitelisted_urlnames:
            return None
        if "Authorization" in request.headers:
            user = authenticate(request)
            if user is not None:
                login(request, user)
                request.user = user
                return None

        return HttpResponseRedirect(reverse("login") + "?next=" + request.path)
