import htmlgenerator as hg
from django.contrib.messages.views import SuccessMessageMixin
from django.utils.translation import gettext as _
from django.views.generic import CreateView
from guardian.mixins import PermissionRequiredMixin

from ..utils import filter_fieldlist
from .util import BaseView, CustomFormMixin


class AddView(
    CustomFormMixin,
    BaseView,
    SuccessMessageMixin,
    PermissionRequiredMixin,
    CreateView,
):
    """TODO: documentation"""

    accept_global_perms = True
    default_success_page = "read"

    def get_success_message(self, cleaned_data):
        return _("Added %s") % self.object

    def __init__(self, *args, **kwargs):
        all = filter_fieldlist(
            kwargs.get("model", getattr(self, "model")), ["__all__"], for_form=True
        )
        self.fields = kwargs.get("fields", getattr(self, "fields", None))
        self.fields = all if self.fields is None else self.fields
        super().__init__(*args, **kwargs)

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.add_{self.model.__name__.lower()}"]

    def get_permission_object(self):
        return None

    def get_context_data(self, *args, **kwargs):
        layout = hg.BaseElement(
            hg.H3(
                _("Add %s") % self.model._meta.verbose_name,
            ),
            self._get_layout_cached(),
        )
        return {
            **super().get_context_data(*args, **kwargs),
            "layout": layout,
            "pagetitle": _("Add %s") % self.model._meta.verbose_name,
        }
