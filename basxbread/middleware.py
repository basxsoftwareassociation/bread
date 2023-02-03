import urllib

try:
    import zoneinfo
except ImportError:
    from backports import zoneinfo  # type: ignore

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import activate, get_language

URL_WHITELIST = (
    "login",
    "password_reset",
    "password_reset_done",
    "password_reset_confirm",
    "password_reset_complete",
    "publicurl",  # for basxbread.contrib.publicurls
) + tuple(getattr(settings, "PUBLIC_URLS", []))


class RequireAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if "basxbread-cookies" not in request.session:
            request.session["basxbread-cookies"] = {}
        for k, v in request.COOKIES.items():
            if k.startswith("basxbread-"):
                request.session["basxbread-cookies"][k] = urllib.parse.unquote(v)

        # load the preferred language for a user and change translation system
        # and language cookie if required
        if request.user and hasattr(request.user, "preferences"):
            lang = request.user.preferences.get("general__preferred_language")
            if lang and lang != get_language():
                # needs to be called before every request to do translation correctly
                activate(lang)
            tz = request.user.preferences.get("general__timezone")
            if tz:
                timezone.activate(zoneinfo.ZoneInfo(tz))
            else:
                timezone.deactivate()

        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.user.is_authenticated:
            return None
        if request.resolver_match.url_name in URL_WHITELIST:
            return None
        if "Authorization" in request.headers:
            user = authenticate(request)
            if user is not None:
                login(request, user)
                request.user = user
                return None

        return HttpResponseRedirect(reverse("login") + "?next=" + request.path)
