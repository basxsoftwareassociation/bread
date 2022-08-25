import urllib

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.generic import RedirectView
from guardian.mixins import PermissionRequiredMixin

from ..utils import reverse_model
from .util import BaseView


class DeleteView(BaseView, PermissionRequiredMixin, RedirectView):
    """TODO: documentation"""

    model = None
    softdeletefield = None  # set to a boolean field on the modle which will be set to True instead of deleting the object
    accept_global_perms = True
    urlparams = (("pk", int),)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # raise exception in case the model has no field with the given name
        if self.softdeletefield:
            self.model._meta.get_field(self.softdeletefield)

    def get_required_permissions(self, request):
        if "restore" in self.request.GET:
            return [
                f"{self.model._meta.app_label}.change_{self.model.__name__.lower()}"
            ]
        return [f"{self.model._meta.app_label}.delete_{self.model.__name__.lower()}"]

    def post(self, *args, **kwargs):
        instance = get_object_or_404(self.model, pk=self.kwargs.get("pk"))
        restore = "restore" in self.request.GET
        if self.softdeletefield:
            setattr(instance, self.softdeletefield, not restore)
            instance.save()
            msg = (
                _("Restored %(modelname)s %(objectname)s")
                if restore
                else _("Deleted %(modelname)s %(objectname)s")
            )
        else:
            instance.delete()
            msg = _("Deleted %(modelname)s %(objectname)s")
        messages.success(
            self.request,
            msg
            % {
                "objectname": instance,
                "modelname": self.model._meta.verbose_name,
            },
        )
        ret = super().post(*args, **kwargs)
        if self.ajax_urlparameter in self.request.GET:
            ret = HttpResponse("OK")
            # This header will be processed by htmx
            # in order to reload the whole page automatically
            ret["HX-Refresh"] = "true"
        return ret

    def get_redirect_url(self, *args, **kwargs):
        if self.request.GET.get("next"):
            return urllib.parse.unquote(self.request.GET["next"])
        if "restore" in self.request.GET and self.softdeletefield:
            return reverse_model(
                self.model, "read", kwargs={"pk": self.kwargs.get("pk")}
            )
        return reverse_model(self.model, "browse")
