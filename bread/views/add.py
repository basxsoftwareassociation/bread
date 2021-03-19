import urllib

import htmlgenerator as hg
from django.contrib.messages.views import SuccessMessageMixin
from django.utils.translation import gettext as _
from django.views.generic import CreateView
from guardian.mixins import PermissionRequiredMixin

from .. import layout as _layout  # prevent name clashing
from ..utils import filter_fieldlist, pretty_modelname, reverse_model
from .util import BreadView, CustomFormMixin


class AddView(
    BreadView,
    CustomFormMixin,
    SuccessMessageMixin,
    PermissionRequiredMixin,
    CreateView,
):
    """TODO: documentation"""

    template_name = "bread/layout.html"
    accept_global_perms = True
    layout = None

    def get_success_message(self, cleaned_data):
        return _("Added %s") % self.object

    def __init__(self, *args, **kwargs):
        self.fields = kwargs.get("fields", getattr(self, "fields", ["__all__"]))
        super().__init__(*args, **kwargs)

    def layout(self, request):
        return hg.BaseElement(
            hg.H3(
                _("Add %s") % pretty_modelname(self.model),
            ),
            _layout.form.Form.wrap_with_form(
                hg.C("form"),
                hg.BaseElement(
                    *[
                        _layout.form.FormField(field)
                        for field in filter_fieldlist(
                            self.model, self.fields, for_form=True
                        )
                    ]
                ),
            ),
        )

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.add_{self.model.__name__.lower()}"]

    def get_permission_object(self):
        return None

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["pagetitle"] = _("Add %s") % pretty_modelname(self.model)
        return context

    def get_success_url(self):
        if self.request.GET.get("next"):
            return urllib.parse.unquote(self.request.GET["next"])
        if self.success_url:
            return self.success_url
        return reverse_model(self.model, "edit", kwargs={"pk": self.object.pk})
