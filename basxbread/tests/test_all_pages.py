# import random
# import uuid
import re
import string

from ddf import G
from django.test import Client, TestCase
from django.urls import get_resolver, reverse
from django_extensions.management.commands import show_urls

ALPHANUMERIC_STR = "".join((string.ascii_letters, string.digits))


def get_real_url(view, urlname, urlpattern):
    arguments = re.findall("<[^>]*>", urlpattern)
    if not arguments:
        return reverse(urlname)
    if hasattr(view, "view_class"):
        # TODO: Hopthesis create form: view.view_class.form_class
        if hasattr(view.view_class, "model"):
            # likely an ID which is required url argument
            if len(arguments) == 1:
                model = view.view_initkwargs.get("model") or view.view_class.model
                urlargname = arguments[0].strip("<>").split(":")[-1]
                obj = G(model)
                return reverse(urlname, kwargs={urlargname: obj.id})
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
            if urlname is None:
                print(f"URL with pattern {urlpattern} has no name")
                continue
            url = get_real_url(view, urlname, urlpattern)
            if url is None:
                print(f"URL {urlname} with pattern {urlpattern} cannot be tested")
            else:
                c.get(url)
                tested += 1
        print(f"Tested URLS: {tested}")
        print(f"Untested URLS: {len(allurls) - tested}")
