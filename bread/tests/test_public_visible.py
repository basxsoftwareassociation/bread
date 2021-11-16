import django.urls
from django.contrib.admindocs.views import simplify_regex
from django.template import TemplateDoesNotExist
from django.test import Client, TestCase
from django_extensions.management.commands import show_urls

ROOT_URLPATTERNS = django.urls.get_resolver(None).url_patterns


class TestAnonymousVisible(TestCase):
    def test_visible(self, urlpatterns=ROOT_URLPATTERNS, prefix=""):
        # get a list of urlpatterns
        url_names = {
            simplify_regex(x[1])
            for x in show_urls.Command().extract_views_from_urlpatterns(
                ROOT_URLPATTERNS
            )
        }

        # exceptions for some pages that can be visible to the public
        # and those pages with dynamic url regex
        # and those out of the bread's scope (e.g., basxconnect)
        url_names = list(
            url_names.difference(
                {
                    "/admin/login/",
                    "/bread/accounts/login",
                    "/bread/auth/password_reset/",
                    "/bread/accounts/password_reset/",
                    "/bread/auth/reset/<uidb64>/<token>/",  # password reset
                    "/bread/auth/password_reset/done/",
                    *(
                        x
                        for x in url_names
                        if not x.startswith("/admin")
                        and not x.startswith("/bread")
                        and not x.startswith("/media")
                        and not x.startswith("/reports")
                    ),
                }
            )
        )

        # try fetching each url and see the response
        c = Client()

        for url in url_names:
            # if any bugs show,
            try:
                response = c.get(url)
                # if the page was redirected to the login page,
                # it's likely invisible to anonymous users.
                self.assertTrue(
                    response.status_code // 100 == 3,
                    "This page %s is visible to anonymous users, with the status code %d"
                    % (url, response.status_code),
                )
            except TemplateDoesNotExist:
                print("The template for %s does not exist." % url)

        print(
            "Public Visibility Test for Bread completed. No confidential pages appears publicly."
        )
