from collections import namedtuple

from django.contrib.auth.models import User
from django.db.models.fields.proxy import OrderWrt
from django.test import Client
from hypothesis import given, settings
from hypothesis.extra.django import TestCase, from_model, register_field_strategy
from hypothesis.strategies import integers

from ..utils.urls import reverse_model

FormField = namedtuple("FormField", ["name", "value", "element", "generators"])


register_field_strategy(OrderWrt, integers(-2147483648, 2147483647))


def authenticate(client):
    user, _ = User.objects.get_or_create(username="admin", is_superuser=True)
    client.force_login(user)


def generic_basxbread_testcase(model, **kwargs):
    class GenericModelTest(TestCase):
        def setUp(self):
            self.client = Client()
            authenticate(self.client)

        @given(from_model(model, **kwargs))
        def test_generic(self, instance):
            self.assertIsNotNone(instance.pk)
            resp = self.client.get(reverse_model(model, "browse"), follow=True)
            self.assertEqual(resp.status_code, 200)
            resp = self.client.get(
                reverse_model(model, "read", kwargs={"pk": instance.pk}), follow=True
            )
            self.assertEqual(resp.status_code, 200)
            resp = self.client.get(
                reverse_model(model, "edit", kwargs={"pk": instance.pk}), follow=True
            )
            resp = self.client.get(
                reverse_model(model, "delete", kwargs={"pk": instance.pk}), follow=True
            )
            self.assertEqual(resp.status_code, 200)

        def test_add(self):
            resp = self.client.get(reverse_model(model, "add"), follow=True)
            self.assertEqual(resp.status_code, 200)
            # TODO: implement add form, use hypothesis

        @given(from_model(model, **kwargs))
        @settings(deadline=None)
        def test_forms(self, instance):
            self.assertIsNotNone(instance.pk)
            # TODO: implement edit form, use hypothesis

    return GenericModelTest
