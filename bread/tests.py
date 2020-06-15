import datetime
import random

from ddf import G, teach
from django.db import models
from django.test import Client, TestCase
from django.urls import reverse
from django.views.generic import CreateView
from django.views.generic.edit import SingleObjectMixin
from django_dynamic_fixture import DDFLibrary
from djmoney.models.fields import CurrencyField, MoneyField
from djmoney.money import Money
from djmoney.settings import CURRENCY_CHOICES

from . import admin


def generate_testable_url(modeladmin, urlname):
    """Returns a callable URL or none if the given URL is not testable"""
    pk_param_name = None
    views = modeladmin.get_views()
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
        if isinstance(modeladmin, admin.BreadGenericAdmin):
            print(
                f"""Warning: Cannot test view {view} because it has multiple parameters
                (presently this test framework can only test very simple views automatically)"""
            )
            return None
        return modeladmin.reverse(urlname, modeladmin.model.objects.first().pk)
    return modeladmin.reverse(urlname)


def register_custom_generators():
    GENERATORS = {
        MoneyField: lambda field: Money(
            (random.random() * 2 - 1) * 999_999_999, random.choice(CURRENCY_CHOICES)[0],
        ),
        CurrencyField: lambda field: random.choice(CURRENCY_CHOICES)[0],
        models.DurationField: lambda field: datetime.timedelta(
            seconds=(random.random() * 2 - 1) * 999_999_999
        ),
    }

    ddflib = DDFLibrary.get_instance()
    # yes, the 3rd level loop is a bit ugly...
    # but necessary because we want to use isinstance and not a dict-lookup
    for modeladmin in admin.site._registry.values():
        if (
            not modeladmin.model._meta.managed
            or modeladmin.model in ddflib.configs
            and DDFLibrary.DEFAULT_KEY in ddflib.configs[modeladmin.model]
        ):
            continue
        lessons = {}
        for field in modeladmin.model._meta.get_fields():
            for fieldtype, generator in GENERATORS.items():
                if isinstance(field, fieldtype):
                    lessons[field.name] = generator
                    break
        teach(modeladmin.model, **lessons)


class BreadAdminTestModels(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        register_custom_generators()

    def test_random_model_creation(self):
        EXAMPLE_COUNT = 20
        for modeladmin in admin.site._registry.values():
            if modeladmin.model._meta.managed:
                for _ in range(EXAMPLE_COUNT):
                    G(modeladmin.model, fill_nullable_fields=True)
                    G(modeladmin.model, fill_nullable_fields=False)


class BreadAdminTestViews(TestCase):
    IGNORE_CODES = [405]  # we do not check results of POST-only views for now

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        register_custom_generators()
        for modeladmin in admin.site._registry.values():
            if modeladmin.model._meta.managed:
                G(modeladmin.model)

    def test_admin_url_protection(self):
        c = Client()
        for modeladmin in admin.site._registry.values():
            if modeladmin.login_required:
                for urlname in modeladmin.get_urls():
                    url = generate_testable_url(modeladmin, urlname)
                    if url:
                        response = c.get(url, follow=True)
                        if response.status_code not in self.IGNORE_CODES:
                            self.assertNotEqual(len(response.redirect_chain), 0, url)
                            self.assertEqual(
                                response.redirect_chain[-1][0].split("?")[0],
                                reverse("login"),
                                url,
                            )

    def test_admin_urls(self):
        c = Client()
        c.login()
        for modeladmin in admin.site._registry.values():
            for urlname, url in modeladmin.get_urls().items():
                url = generate_testable_url(modeladmin, urlname)
                if url:
                    response = c.get(url, follow=True)
                    if response.status_code not in self.IGNORE_CODES:
                        self.assertEqual(response.status_code, 200, f"{urlname}: {url}")
