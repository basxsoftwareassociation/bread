"""
Bread comes with a list of "improved" django views. All views are based
on the standard class-based views of django and are should easily be
extendable and composable by subclassing them. Most of the views require
an argument "admin" which is an instance of the according BreadAdmin class
"""
import urllib

from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import CreateView
from guardian.mixins import PermissionRequiredMixin

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
    template_name = "carbon_design/form.html"
    admin = None
    accept_global_perms = True

    def get_success_message(self, cleaned_data):
        return f"Added {self.object}"

    def __init__(self, admin, *args, **kwargs):
        self.admin = admin
        self.model = admin.model
        field_config = kwargs.get("layout", self.layout)
        if not isinstance(field_config, plisplate.BaseElement):
            self.layout = plisplate.form.Form.from_fieldnames(
                filter_fieldlist(self.model, field_config, for_form=True)
            )
        else:
            self.layout = field_config
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
