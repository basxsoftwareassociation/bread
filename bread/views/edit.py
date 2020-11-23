"""
Bread comes with a list of "improved" django views. All views are based
on the standard class-based views of django and are should easily be
extendable and composable by subclassing them. Most of the views require
an argument "admin" which is an instance of the according BreadAdmin class
"""
import urllib

from guardian.mixins import PermissionRequiredMixin

from django.contrib.messages.views import SuccessMessageMixin
from django.utils.translation import gettext as _
from django.views.generic import UpdateView

from .. import layout as _layout  # prevent name clashing
from ..utils import CustomizableClass, filter_fieldlist
from .util import CustomFormMixin


class EditView(
    CustomizableClass,
    CustomFormMixin,
    SuccessMessageMixin,
    PermissionRequiredMixin,
    UpdateView,
):
    template_name = "bread/layout.html"
    admin = None
    accept_global_perms = True
    layout = None

    def get_success_message(self, cleaned_data):
        return f"Saved {self.object}"

    def __init__(self, admin, *args, **kwargs):
        self.admin = admin
        self.model = admin.model
        layout = kwargs.get("layout", self.layout)
        if not isinstance(layout, _layout.BaseElement):
            layout = _layout.BaseElement(
                *[
                    _layout.form.FormField(field)
                    for field in filter_fieldlist(self.model, layout, for_form=True)
                ]
            )
        self.layout = _layout.BaseElement(
            _layout.H2(
                _("Edit"),
                " ",
                self.admin.verbose_modelname,
                " ",
                _layout.I(_layout.F(lambda e, c: c["object"])),
            ),
            _layout.form.Form.wrap_with_form(_layout.C("form"), layout),
        )
        super().__init__(*args, **kwargs)

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.change_{self.model.__name__.lower()}"]

    def get_success_url(self):
        if "quicksave" in self.request.POST:
            return self.request.get_full_path()
        if self.request.GET.get("next"):
            return urllib.parse.unquote(self.request.GET["next"])
        return self.admin.reverse("index")
