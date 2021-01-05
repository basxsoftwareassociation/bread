"""
Bread comes with a list of "improved" django views. All views are based
on the standard class-based views of django and are should easily be
extendable and composable by subclassing them. Most of the views require
an argument "admin" which is an instance of the according BreadAdmin class
"""
import urllib
import warnings

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import DeleteView as DjangoDeleteView
from guardian.mixins import PermissionRequiredMixin

from ..utils import reverse_model
from .util import BreadView


class DeleteView(
    BreadView, PermissionRequiredMixin, SuccessMessageMixin, DjangoDeleteView
):
    template_name = "bread/confirm_delete.html"
    accept_global_perms = True
    urlparams = (("pk", int),)

    def layout(self, request):
        return None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.delete_{self.model.__name__.lower()}"]

    def get_success_url(self):
        messages.info(self.request, f"Deleted {self.object}")
        if self.request.GET.get("next"):
            return urllib.parse.unquote(self.request.GET["next"])
        return reverse_model(self.model, "browse")


warnings.warn(
    f"{DeleteView} needs to implement the layout method propertly in the future, see https://github.com/basxsoftwareassociation/bread/issues/7"
)
