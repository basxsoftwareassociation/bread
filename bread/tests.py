from ddf import G
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.http import urlencode
from django.views.generic import CreateView
from django.views.generic.edit import SingleObjectMixin

from . import admin


def generate_testable_url(admin, urlname):
    """Returns a callable URL or none if the given URL is not testable"""
    pk_param_name = None
    views = admin.get_views()
    if urlname not in views:
        return None
    view = views[urlname]
    if hasattr(view, "view_class"):
        if issubclass(view.view_class, SingleObjectMixin) and not issubclass(
            view.view_class, CreateView
        ):
            pk_param_name = view.view_class.pk_url_kwarg
        if "urlparams" in view.view_initkwargs:
            print(
                f"Warning: Cannot test view {view} because it uses 'urlparams': {view.view_initkwargs['urlparams']}"
            )
            return None
    elif callable(view):
        params = view.__code__.co_varnames[1 : view.__code__.co_argcount]
        if len(params) > 1:
            print(
                f"""Warning: Cannot test view {view} because it has multiple parameters
                (presently this test framework can only test very simple views automatically)"""
            )
            return None
        for param in params:
            pk_param_name = param
    if pk_param_name is not None:
        return admin.reverse(urlname, admin.model.objects.first().pk)
    return admin.reverse(urlname)


class BreadAdminTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        for modeladmin in admin.site._registry.values():
            G(modeladmin.model)

    def test_admin_url_protection(self):
        c = Client()
        for modeladmin in admin.site._registry.values():
            for urlname in modeladmin.get_urls():
                url = generate_testable_url(modeladmin, urlname)
                if url:
                    response = c.get(url)
                    self.assertRedirects(
                        response, f"{reverse('login')}?{urlencode({'next': url})}"
                    )

    def test_admin_urls(self):
        c = Client()
        c.login()
        for modeladmin in admin.site._registry.values():
            for urlname, url in modeladmin.get_urls().items():
                url = generate_testable_url(modeladmin, urlname)
                if url:
                    response = c.get(url, follow=True)
                    self.assertEqual(response.status_code, 200, f"{urlname}: {url}")
