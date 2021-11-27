# import random
# import uuid
import re
import string

from django.test import Client, TestCase
from django.urls import get_resolver, reverse
from django_extensions.management.commands import show_urls

ALPHANUMERIC_STR = "".join((string.ascii_letters, string.digits))


def get_real_url(view, urlname, urlpattern):
    arguments = re.findall("<[^>]*>", urlpattern)
    if not arguments:
        return reverse(urlname)
    return None


class TestAllURLs(TestCase):
    # get a list of urlpatterns

    def test_allurls(self):
        tested = 0
        allurls = show_urls.Command().extract_views_from_urlpatterns(
            get_resolver(None).url_patterns
        )
        c = Client()
        for (
            view,
            urlpattern,
            urlname,
        ) in allurls:
            url = get_real_url(view, urlname, urlpattern)
            if url is None:
                print(f"URL {urlname} with pattern {urlpattern} cannot be tested")
            else:
                c.get(url)
                tested += 1
        print(f"Tested URLS: {tested}")
        print(f"Untested URLS: {len(allurls) - tested}")
