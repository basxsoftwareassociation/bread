import urllib

from guardian.mixins import PermissionRequiredMixin

from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic import CreateView

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
        self.fields = kwargs.get("fields", getattr(self, "fields", ["__all__"]))
        super().__init__(*args, **kwargs)

    def layout(self, request):
        return _layout.BaseElement(
            _layout.H3(
                _("Add %s") % pretty_modelname(self.model),
            ),
            _layout.form.Form.wrap_with_form(
                _layout.C("form"),
                _layout.BaseElement(
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

    def get_success_url(self):
        if self.request.GET.get("next"):
            return urllib.parse.unquote(self.request.GET["next"])
        return reverse(model_urlname(self.model, "browse"))
