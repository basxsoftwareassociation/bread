import random
import string
import traceback
import uuid

import django.urls
from django.contrib.admindocs.views import simplify_regex
from django.http import HttpResponseRedirect
from django.template import TemplateDoesNotExist
from django.test import Client, TestCase
from django_extensions.management.commands import show_urls

ROOT_URLPATTERNS = django.urls.get_resolver(None).url_patterns
ALPHANUMERIC_STR = "".join((string.ascii_letters, string.digits))


class TestAnonymousVisible(TestCase):
    # get a list of urlpatterns

    def test_visible(self):
        ALL_URLS = {
            x[2]: simplify_regex(x[1])  # { urlname: urlpattern }
            for x in show_urls.Command().extract_views_from_urlpatterns(
                ROOT_URLPATTERNS
            )
        }
        EXCEPTED_URLPATTERNS = {
            ALL_URLS[exclude]
            for exclude in (
                "admin:login",
                "login",
                "password_reset",
                "password_reset_done",
                "password_reset_complete",
                "password_reset_confirm",
            )
            if exclude in ALL_URLS
        }

        # update the exceptions for some pages that can be visible to the public
        # and those pages with dynamic url regex
        # and those out of the basxbread's scope (e.g., basxconnect)
        url_names = {ALL_URLS[x] for x in ALL_URLS} - EXCEPTED_URLPATTERNS

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
                        # the line above can be avoided by bandit because
                        # it isn't for security purposes.
                    elif t == "uuid":
                        args[i] = str(uuid.uuid4())
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
                # there's some errors loading those pages
                # However, 404 can happen with certain urls, make an exception
                if response.status_code == 404:
                    continue
                self.assertTrue(
                    not 400 <= response.status_code <= 499,
                    "This page %s failed to load, with status code %d."
                    % (url, response.status_code),
                )
                # if the status code is 3, and the Location is ALL_URLS["login"]
                # it's likely invisible to anonymous users, as the page
                # redirects to the login page.
                self.assertTrue(
                    300 <= response.status_code <= 399
                    and isinstance(response, HttpResponseRedirect)
                    and response.url.startswith(str(ALL_URLS["login"])),
                    "This page %s may be visible to anonymous users, with the status code %d"
                    % (url, response.status_code),
                )

            except TemplateDoesNotExist as e:
                traceback.print_exc()

                if hasattr(e, "message"):
                    print("The template for", url, "at", e.message, "does not exist.")
                else:
                    print("The template for", url, "does not exist.")
