import re
import urllib

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils.translation import pgettext_lazy
from django.views.decorators.cache import never_cache
from django.views.generic import UpdateView
from guardian.mixins import PermissionRequiredMixin

from ..utils import filter_fieldlist, model_urlname, reverse_model
from .util import BreadView, CustomFormMixin


class EditView(
    CustomFormMixin,
    BreadView,
    messages.views.SuccessMessageMixin,
    PermissionRequiredMixin,
    UpdateView,
):
    """TODO: documentation"""

    template_name = "bread/base.html"
    accept_global_perms = True
    fields = None
    urlparams = (("pk", int),)

    def __init__(self, *args, **kwargs):
        all = filter_fieldlist(kwargs.get("model"), ["__all__"])
        self.fields = kwargs.get("fields", getattr(self, "fields", None))
        self.fields = all if self.fields is None else self.fields
        super().__init__(*args, **kwargs)

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.change_{self.model.__name__.lower()}"]

    def get_context_data(self, *args, **kwargs):
        return {
            **super().get_context_data(*args, **kwargs),
            "layout": self.get_layout(),
            "pagetitle": str(self.object),
        }

    def get_success_message(self, cleaned_data):
        return f"Saved {self.object}"

    # prevent browser caching edit views
    @never_cache
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


def generate_copyview(model, attrs=None, labelfield=None, copy_related_fields=()):
    """creates a copy of a model instance and redirects to the edit view of the newly created instance
    attrs: custom field values for the new instance
    labelfield: name of a model field which will be used to create copy-labels (Example, Example (Copy 2), Example (Copy 3), etc)
    """
    attrs = attrs or {}

    def copy(request, pk: int):
        instance = get_object_or_404(model, pk=pk)
        if labelfield:
            attrs[labelfield] = copylabel(getattr(instance, labelfield))
        try:
            clone = deepcopy_object(instance, attrs, copy_related_fields)
        except Exception as e:
            messages.error(request, e)
            if request.GET.get("next"):
                return redirect(urllib.parse.unquote(request.GET["next"]))
            return redirect(reverse_model(model, "browse"))
        if request.GET.get("next"):
            return redirect(urllib.parse.unquote(request.GET["next"]))
        messages.success(request, _("Created copy %s" % instance))
        return redirect(reverse(model_urlname(model, "read"), args=[clone.pk]))

    return copy


def generate_bulkcopyview(
    model, pk_queryname="selected", attrs=None, labelfield=None, copy_related_fields=()
):
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
            if labelfield:
                attrs[labelfield] = copylabel(getattr(instance, labelfield))
            try:
                deepcopy_object(instance, attrs, copy_related_fields)
                created += 1
            except Exception as e:
                messages.error(request, e)
                errors += 1
            messages.success(request, _("Created %s copies" % created))
        return redirect(reverse(model_urlname(model, "browse")))

    return copy


def deepcopy_object(instance, attrs=None, copy_related_fields=()):
    """
    Creates a 'deep' coyp of the model instance
    Related fields are only copied if they are listed in copy_related_fields
    ManyToMany relationships are copied automatically if they have no key in 'attrs'
    attrs defineds default values for fields
    """
    oldpk = instance.pk
    # see https://docs.djangoproject.com/en/3.2/topics/db/queries/#copying-model-instances
    many2manyfields = {
        f.name: getattr(instance, f.name).all()
        for f in instance._meta.get_fields()
        if f.many_to_many
    }
    instance.pk = None
    instance.id = None
    instance._state.adding = True
    for k, v in (attrs or {}).items():
        setattr(instance, k, v)
    instance.save()
    for field, queryset in many2manyfields.items():
        getattr(instance, field).set(queryset)

    oldinstance = type(instance).objects.get(pk=oldpk)
    for field in copy_related_fields:
        related_name = oldinstance._meta.get_field(field).field.name
        for obj in getattr(oldinstance, field).all():
            obj.pk = None
            obj.id = None
            obj._state.adding = True
            setattr(obj, related_name, instance)
            obj.save()

    instance.save()
    return instance


def copylabel(original_name):
    """create names/labels with the sequence (Copy), (Copy 2), (Copy 3), etc."""
    copylabel = pgettext_lazy("this is a copy", "Copy")
    copy_re = f"\\({copylabel}( [0-9]*)?\\)"
    match = re.search(copy_re, original_name)
    if match is None:
        label = f"{original_name} ({copylabel})"
    elif match.groups()[0] is None:
        label = re.sub(copy_re, f"({copylabel} 2)", original_name)
    else:
        n = int(match.groups()[0].strip()) + 1
        label = re.sub(copy_re, f"({copylabel} {n})", original_name)
    return label
