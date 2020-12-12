"""
Bread comes with a list of "improved" django views. All views are based
on the standard class-based views of django and are should easily be
extendable and composable by subclassing them. Most of the views require
an argument "admin" which is an instance of the according BreadAdmin class
"""
import urllib

from guardian.mixins import PermissionRequiredMixin

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import DeleteView as DjangoDeleteView

from ..utils import CustomizableClass
from ..utils.urls import reverse_model


class DeleteView(
    CustomizableClass, PermissionRequiredMixin, SuccessMessageMixin, DjangoDeleteView
):
    template_name = "bread/confirm_delete.html"
    admin = None
    accept_global_perms = True
    urlparams = (("pk", int),)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.delete_{self.model.__name__.lower()}"]

    def get_success_url(self):
        messages.info(self.request, f"Deleted {self.object}")
        if self.request.GET.get("next"):
            return urllib.parse.unquote(self.request.GET["next"])
        return reverse_model(self.model, "browse")
