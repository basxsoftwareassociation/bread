"""
Bread comes with a list of "improved" django views. All views are based
on the standard class-based views of django and are should easily be
extendable and composable by subclassing them. Most of the views require
an argument "admin" which is an instance of the according BreadAdmin class
"""
import urllib

from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic import CreateView
from guardian.mixins import PermissionRequiredMixin

from .. import layout as _layout  # prevent name clashing
from ..utils import CustomizableClass, filter_fieldlist, pretty_modelname
from ..utils.urls import model_urlname
from .util import CustomFormMixin


class AddView(
    CustomizableClass,
    CustomFormMixin,
    SuccessMessageMixin,
    PermissionRequiredMixin,
    CreateView,
):
    template_name = "bread/layout.html"
    accept_global_perms = True
    layout = None

    def get_success_message(self, cleaned_data):
        return _("Added %s") % self.object

    def __init__(self, *args, **kwargs):
        model = kwargs["model"]
        layout = kwargs.get("layout", self.layout)
        layout = layout() if callable(layout) else layout
        if not isinstance(layout, _layout.BaseElement):
            layout = _layout.BaseElement(
                *[
                    _layout.form.FormField(field)
                    for field in filter_fieldlist(model, layout, for_form=True)
                ]
            )
        self.layout = _layout.BaseElement(
            _layout.H2(
                _("Add %s") % pretty_modelname(model),
            ),
            _layout.form.Form.wrap_with_form(_layout.C("form"), layout),
        )
        super().__init__(*args, **kwargs)

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.add_{self.model.__name__.lower()}"]

    def get_permission_object(self):
        return None

    def get_success_url(self):
        if self.request.GET.get("next"):
            return urllib.parse.unquote(self.request.GET["next"])
        return reverse(model_urlname(self.model, "browse"))
