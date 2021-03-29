"""
Bread comes with a list of "improved" django views. All views are based
on the standard class-based views of django and are should easily be
extendable and composable by subclassing them. Most of the views require
an argument "admin" which is an instance of the according BreadAdmin class
"""
import urllib

from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.generic import RedirectView
from djangoql.queryset import apply_search
from guardian.mixins import PermissionRequiredMixin

from ..utils import pretty_modelname, reverse_model
from .util import BreadView


class DeleteView(BreadView, PermissionRequiredMixin, RedirectView):
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
        return [f"{self.model._meta.app_label}.delete_{self.model.__name__.lower()}"]

    def get(self, *args, **kwargs):
        instance = get_object_or_404(self.model, pk=self.kwargs.get("pk"))
        if self.softdeletefield:
            setattr(instance, self.softdeletefield, True)
            instance.save()
        else:
            instance.delete()
        messages.success(
            self.request,
            _("Deleted %(modelname)s %(objectname)s")
            % {
                "objectname": instance,
                "modelname": pretty_modelname(self.model),
            },
        )
        return super().get(*args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        if self.request.GET.get("next"):
            return urllib.parse.unquote(self.request.GET["next"])
        return reverse_model(self.model, "browse")


class BulkDeleteView(
    PermissionRequiredMixin,
    RedirectView,
):
    objectids_urlparameter = "selected"  # see bread/static/js/main.js:submitbulkaction
    query_urlparameter = "q"
    accept_global_perms = True
    model = None
    softdeletefield = None

    def __init__(self, model, *args, **kwargs):
        self.query_urlparameter = (
            kwargs.get("query_urlparameter") or self.query_urlparameter
        )
        self.objectids_urlparameter = (
            kwargs.get("objectids_urlparameter") or self.objectids_urlparameter
        )
        super().__init__(*args, **kwargs)
        self.model = model
        if self.softdeletefield:
            self.model._meta.get_field(self.softdeletefield)

    def get(self, *args, **kwargs):
        deleted = 0
        for instance in self.get_queryset():
            try:
                if not self.request.user.has_perm(
                    self.get_required_permissions(self.request), instance
                ):
                    raise Exception(
                        _("Your user has not the permissions to delete %s") % instance
                    )
                if self.softdeletefield:
                    setattr(instance, self.softdeletefield, True)
                    instance.save()
                else:
                    instance.delete()
                deleted += 1
            except Exception as e:
                messages.error(
                    self.request,
                    _("%s could not be deleted: %s") % (object, e),
                )

        messages.success(
            self.request,
            _("Deleted %(count)s %(modelname)s")
            % {
                "count": deleted,
                "modelname": pretty_modelname(self.model, plural=deleted > 1),
            },
        )
        return super().get(*args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        if self.url:
            return super().get_redirect_url(*args, **kwargs)
        return reverse_model(self.model, "browse")

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.delete_{self.model.__name__.lower()}"]

    def get_queryset(self):
        """Prefetch related tables to speed up queries. Also order result by get-parameters."""
        qs = self.model.objects.all()
        if self.query_urlparameter in self.request.GET:
            qs = apply_search(
                qs,
                "("
                + ") and (".join(self.request.GET.getlist(self.query_urlparameter))
                + ")",
            )
        selectedobjects = self.request.GET.getlist(self.objectids_urlparameter)
        if selectedobjects and "all" not in selectedobjects:
            qs &= self.model.objects.filter(pk__in=selectedobjects)

        return qs
