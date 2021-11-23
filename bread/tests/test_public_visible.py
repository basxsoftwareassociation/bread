import secrets
import traceback

import django.urls
from django.contrib.admindocs.views import simplify_regex
from django.template import TemplateDoesNotExist
from django.test import Client, TestCase
from django.urls import reverse_lazy as reverse
from django_extensions.management.commands import show_urls

ROOT_URLPATTERNS = django.urls.get_resolver(None).url_patterns


class TestAnonymousVisible(TestCase):
    # get a list of urlpatterns
    ALL_URL_NAMES = {
        simplify_regex(x[1])
        for x in show_urls.Command().extract_views_from_urlpatterns(ROOT_URLPATTERNS)
    }
    EXCEPTED_URLPATTERNS = {
        reverse("admin:login"),
        reverse("django_auth:password_reset"),
        reverse("django_auth:password_reset_done"),
        reverse("django_auth:password_reset_complete"),
        reverse(
            "django_auth:password_reset_confirm",
            args=["(?P<uidb64>[^/]+)", "(?P<token>[^/]+)"],
        ),
        reverse("login"),
        reverse("password_reset"),
        reverse("password_reset_done"),
        reverse("password_reset_complete"),
        reverse("password_reset_confirm", args=["<uidb64>", "<token>"]),
        # TODO: figure out the way to manage this view.
        "/bread/preferences/global/<slug:section>",
    }

    def test_visible(self):

        print(*self.EXCEPTED_URLPATTERNS, sep="\n")

        # add the uncompiled url to exception
        excepted_urlpatterns = self.EXCEPTED_URLPATTERNS.copy()
        url_intpk = {x for x in self.ALL_URL_NAMES if "<int:pk>" in x}

        # update the exceptions for some pages that can be visible to the public
        # and those pages with dynamic url regex
        # and those out of the bread's scope (e.g., basxconnect)
        url_names = self.ALL_URL_NAMES - excepted_urlpatterns - url_intpk

        # manually add a list of urls with a dynamic subdirectory.
        # (e.g., <int:pk>)
        for url in url_intpk:
            url_names.add(url.replace("<int:pk>", str(secrets.randbelow(100))))

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
                    and response.headers["Location"].startswith(
                        "/bread/accounts/login/"
                    ),
                    "This page %s may be visible to anonymous users, with the status code %d"
                    % (url, response.status_code),
                )

                # print(url, "checked")

            except TemplateDoesNotExist as e:
                if hasattr(e, "message"):
                    print("The template for", url, "at", e.message, "does not exist.")
                else:
                    print("The template for", url, "does not exist.")

                traceback.print_exc()
