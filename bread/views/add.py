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
from django.views.generic import CreateView

from ..layout.components import plisplate
from ..utils import CustomizableClass, filter_fieldlist
from .util import CustomFormMixin


class AddView(
    CustomizableClass,
    CustomFormMixin,
    SuccessMessageMixin,
    PermissionRequiredMixin,
    CreateView,
):
    template_name = "carbon_design/dynamic_layout.html"
    admin = None
    accept_global_perms = True
    layout = None

    def get_success_message(self, cleaned_data):
        return f"Added {self.object}"

    def __init__(self, admin, *args, **kwargs):
        self.admin = admin
        self.model = admin.model
        layout = kwargs.get("layout", self.layout)
        if not isinstance(layout, plisplate.BaseElement):
            layout = [
                plisplate.form.FormField(field)
                for field in filter_fieldlist(self.model, layout, for_form=True)
            ]
        self.layout = plisplate.BaseElement(
            plisplate.H2(_("Add"), " ", self.admin.verbose_modelname,),
            plisplate.form.Form.wrap_with_form(plisplate.C("form"), layout),
        )
        super().__init__(*args, **kwargs)

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.add_{self.model.__name__.lower()}"]

    def get_permission_object(self):
        return None

    def get_success_url(self):
        if "quicksave" in self.request.POST:
            return self.admin.reverse(
                "edit", pk=self.object.id, query_arguments=self.request.GET
            )
        if self.request.GET.get("next"):
            return urllib.parse.unquote(self.request.GET["next"])
        return self.admin.reverse("index")
