"""
Bread comes with a list of "improved" django views. All views are based
on the standard class-based views of django and are should easily be
extendable and composable by subclassing them. Most of the views require
an argument "admin" which is an instance of the according BreadAdmin class
"""
import urllib

from crispy_forms.layout import Layout
from crispy_forms.utils import TEMPLATE_PACK
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import CreateView
from django.views.generic import DeleteView as DjangoDeleteView
from guardian.mixins import PermissionRequiredMixin

from ..utils import CustomizableClass, filter_fieldlist
from .util import CustomFormMixin


class AddView(
    CustomizableClass,
    CustomFormMixin,
    SuccessMessageMixin,
    PermissionRequiredMixin,
    CreateView,
):
    template_name = f"{TEMPLATE_PACK}/form.html"
    admin = None
    accept_global_perms = True

    def get_success_message(self, cleaned_data):
        return f"Added {self.object}"

    def __init__(self, admin, *args, **kwargs):
        self.admin = admin
        self.model = admin.model
        field_config = kwargs.get("fields", self.fields)
        if not isinstance(field_config, Layout):
            self.layout = Layout(
                *filter_fieldlist(self.model, field_config, for_form=True)
            )
        else:
            self.layout = field_config
        self.fields = [i[1] for i in self.layout.get_field_names()]
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


class DeleteView(
    CustomizableClass, PermissionRequiredMixin, SuccessMessageMixin, DjangoDeleteView
):
    template_name = f"{TEMPLATE_PACK}/confirm_delete.html"
    admin = None
    accept_global_perms = True

    def __init__(self, admin, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.admin = admin

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.delete_{self.model.__name__.lower()}"]

    def get_success_url(self):
        messages.info(self.request, f"Deleted {self.object}")
        if self.request.GET.get("next"):
            return urllib.parse.unquote(self.request.GET["next"])
        return self.admin.reverse("index")
