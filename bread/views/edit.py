"""
Bread comes with a list of "improved" django views. All views are based
on the standard class-based views of django and are should easily be
extendable and composable by subclassing them. Most of the views require
an argument "admin" which is an instance of the according BreadAdmin class
"""
import urllib

from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.views.generic import UpdateView
from guardian.mixins import PermissionRequiredMixin

from .. import layout as _layout  # prevent name clashing
from ..utils import model_urlname
from .util import BreadView, CustomFormMixin


class EditView(
    BreadView,
    CustomFormMixin,
    SuccessMessageMixin,
    PermissionRequiredMixin,
    UpdateView,
):
    template_name = "bread/layout.html"
    accept_global_perms = True
    fields = None
    urlparams = (("pk", int),)

    def get_success_message(self, cleaned_data):
        return f"Saved {self.object}"

    def __init__(self, *args, **kwargs):
        self.fields = kwargs.get("fields", getattr(self, "fields", ["__all__"]))
        super().__init__(*args, **kwargs)

    def layout(self, request):
        return _layout.ObjectContext(
            self.object,
            _layout.BaseElement(
                _layout.grid.Grid(
                    _layout.grid.Row(
                        _layout.grid.Col(
                            _layout.H3(
                                _layout.I(_layout.F(lambda c, e: c["object"])),
                            )
                        )
                    ),
                ),
                _layout.form.Form.wrap_with_form(
                    _layout.C("form"), self.formlayout(request)
                ),
            ),
        )

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.change_{self.model.__name__.lower()}"]

    def get_success_url(self):
        if self.request.GET.get("next"):
            return urllib.parse.unquote(self.request.GET["next"])
        return reverse(model_urlname(self.model, "browse"))
