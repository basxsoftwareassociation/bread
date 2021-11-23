import random
import traceback

import django.urls
from django.contrib.admindocs.views import simplify_regex
from django.http import HttpResponseRedirect
from django.template import TemplateDoesNotExist
from django.test import Client, TestCase
from django.urls import reverse_lazy as reverse
from django_extensions.management.commands import show_urls

ROOT_URLPATTERNS = django.urls.get_resolver(None).url_patterns
ALPHANUMERIC_STR = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"


class TestAnonymousVisible(TestCase):
    # get a list of urlpatterns
    ALL_URL_NAMES = {
        simplify_regex(x[1])
        for x in show_urls.Command().extract_views_from_urlpatterns(ROOT_URLPATTERNS)
    }
    EXCEPTED_URLPATTERNS = {
        reverse("admin:login"),
        reverse("login"),
        reverse("password_reset"),
        reverse("password_reset_done"),
        reverse("password_reset_complete"),
        "/bread/accounts/reset/<uidb64>/<token>/",
    }

    def test_visible(self):

        # update the exceptions for some pages that can be visible to the public
        # and those pages with dynamic url regex
        # and those out of the bread's scope (e.g., basxconnect)
        url_names = self.ALL_URL_NAMES - self.EXCEPTED_URLPATTERNS

        # this tricky way works because '<' will always be encoded
        # if being requested, except for Django url patterns.
        url_with_args = {x for x in url_names if "<" in x}

        for url in url_with_args:
            args = [x for x in url.split("/")]
            for i in range(len(args)):
                if "<" not in args[i]:
                    continue

                if ":" in args[i]:  # the first one will specify its type
                    t = args[i][1 : args[i].find(":")]

                    if t == "int":
                        args[i] = str(random.randint(1, 100))  # nosec
                        # the line above can be omitted because it isn't for
                        # security purposes.
                    else:
                        args[i] = "".join(random.sample(ALPHANUMERIC_STR, k=10))

                else:
                    args[i] = "".join(random.sample(ALPHANUMERIC_STR, k=10))

            url_names.add("/".join(args))

        # remove url with unsubstituted arguments
        url_names -= url_with_args

        # try fetching each url and see the response
        c = Client()

        for url in url_names:
            try:
                response = c.get(url)
                # if the status code is 4,
                # there's some errors loading that pages
                self.assertTrue(
                    not 400 <= response.status_code <= 499,
                    "This page %s failed to load, with status code %d."
                    % (url, response.status_code),
                )
                # if the status code is 3, and the Location is /bread/accounts/login/
                # it's likely invisible to anonymous users, as the page
                # redirects to the login page.
                self.assertTrue(
                    300 <= response.status_code <= 399
                    and isinstance(response, HttpResponseRedirect)
                    and response.url.startswith(str(reverse("login"))),
                    "This page %s may be visible to anonymous users, with the status code %d"
                    % (url, response.status_code),
                )

            except TemplateDoesNotExist as e:
                if hasattr(e, "message"):
                    print("The template for", url, "at", e.message, "does not exist.")
                else:
                    print("The template for", url, "does not exist.")

                traceback.print_exc()