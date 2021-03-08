"""
Bread comes with a list of "improved" django views. All views are based
on the standard class-based views of django and are should easily be
extendable and composable by subclassing them. Most of the views require
an argument "admin" which is an instance of the according BreadAdmin class
"""
import re
import urllib

import htmlgenerator as hg
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.generic import UpdateView
from guardian.mixins import PermissionRequiredMixin
from model_clone.utils import create_copy_of_instance

from .. import layout as _layout  # prevent name clashing
from ..utils import filter_fieldlist, model_urlname
from .util import BreadView, CustomFormMixin


class EditView(
    BreadView,
    CustomFormMixin,
    messages.views.SuccessMessageMixin,
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
        all = filter_fieldlist(kwargs.get("model"), ["__all__"])
        self.fields = kwargs.get("fields", getattr(self, "fields", None)) or all
        super().__init__(*args, **kwargs)

    def layout(self, request):
        return hg.BaseElement(
            _layout.grid.Grid(
                _layout.grid.Row(
                    _layout.grid.Col(
                        hg.H3(
                            hg.I(hg.F(lambda c, e: c["object"])),
                        )
                    )
                ),
            ),
            _layout.form.Form.wrap_with_form(hg.C("form"), self.formlayout(request)),
        )

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.change_{self.model.__name__.lower()}"]

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["pagetitle"] = str(self.object)
        return context

    def get_success_url(self):
        if self.request.GET.get("next"):
            return urllib.parse.unquote(self.request.GET["next"])
        return reverse(model_urlname(self.model, "read"), kwargs={"pk": self.object.pk})

    # prevent browser caching edit views
    @never_cache
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


def generate_copyview(model, attrs=None, labelfield=None):
    """creates a copy of a model instance and redirects to the edit view of the newly created instance
    attrs: custom field values for the new instance
    labelfield: name of a model field which will be used to create copy-labels (Example, Example (Copy 2), Example (Copy 3), etc)
    """
    attrs = attrs or {}

    def copy(request, pk: int):
        instance = get_object_or_404(model, pk=pk)
        # create labels with the sequence (Copy), (Copy 2), (Copy 3), etc.
        if labelfield:
            copylabel = _("Copy")
            copy_re = f"\\({copylabel}( [0-9]*)?\\)"
            match = re.search(copy_re, instance.name)
            if match is None:
                label = f"{instance.name} ({copylabel})"
            elif match.groups()[0] is None:
                label = re.sub(copy_re, f"({copylabel} 2)", instance.name)
            else:
                n = int(match.groups()[0].strip()) + 1
                label = re.sub(copy_re, f"({copylabel} {n})", instance.name)
            attrs[labelfield] = label

        clone = create_copy_of_instance(instance, attrs=attrs)
        return redirect(reverse(model_urlname(model, "edit"), args=[clone.pk]))

    return copy


def generate_bulkcopyview(model, pk_queryname="selected", attrs=None, labelfield=None):
    """creates a copy of a list of instances and redirects to the edit view of the newly created instance
    pk_queryname: name of the HTTP query parameter which carries the pk's of the object to duplicate
    attrs: custom field values for the new instance
    labelfield: name of a model field which will be used to create copy-labels (Example, Example (Copy 2), Example (Copy 3), etc)
    """
    attrs = attrs or {}

    def copy(request):
        created = 0
        errors = 0
        for pk in request.GET.getlist(pk_queryname):
            instance = get_object_or_404(model, pk=pk)
            # create labels with the sequence (Copy), (Copy 2), (Copy 3), etc.
            if labelfield:
                copylabel = _("Copy")
                copy_re = f"\\({copylabel}( [0-9]*)?\\)"
                match = re.search(copy_re, instance.name)
                if match is None:
                    label = f"{instance.name} ({copylabel})"
                elif match.groups()[0] is None:
                    label = re.sub(copy_re, f"({copylabel} 2)", instance.name)
                else:
                    n = int(match.groups()[0].strip()) + 1
                    label = re.sub(copy_re, f"({copylabel} {n})", instance.name)
                attrs[labelfield] = label
            try:
                create_copy_of_instance(instance, attrs=attrs)
                created += 1
            except Exception as e:
                messages.error(request, e)
                errors += 1
            messages.success(request, _("Created %s copies" % created))
        return redirect(reverse(model_urlname(model, "browse")))

    return copy
