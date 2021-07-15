import htmlgenerator as hg
from django.contrib.messages.views import SuccessMessageMixin
from django.utils.translation import gettext as _
from django.views.generic import CreateView
from guardian.mixins import PermissionRequiredMixin

from ..utils import pretty_modelname
from .util import BreadView, CustomFormMixin


class AddView(
    CustomFormMixin,
    BreadView,
    SuccessMessageMixin,
    PermissionRequiredMixin,
    CreateView,
):
    """TODO: documentation"""

    accept_global_perms = True

    def get_success_message(self, cleaned_data):
        return _("Added %s") % self.object

    def __init__(self, *args, **kwargs):
        self.fields = kwargs.get("fields", getattr(self, "fields", ["__all__"]))
        super().__init__(*args, **kwargs)

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.add_{self.model.__name__.lower()}"]

    def get_permission_object(self):
        return None

    def get_context_data(self, *args, **kwargs):
        layout = hg.BaseElement(
            hg.H3(
                _("Add %s") % pretty_modelname(self.model),
            ),
            self._get_layout_cached(),
        )
        return {
            **super().get_context_data(*args, **kwargs),
            "layout": layout,
            "pagetitle": _("Add %s") % pretty_modelname(self.model),
        }
