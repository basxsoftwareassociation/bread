from django.views.generic import DetailView
from guardian.mixins import PermissionRequiredMixin

from .. import layout as _layout  # prevent name clashing
from ..utils import (
    filter_fieldlist,
    pretty_fieldname,
    pretty_modelname,
    resolve_relationship,
)
from .util import BreadView


class ReadView(BreadView, PermissionRequiredMixin, DetailView):
    fields = None
    accept_global_perms = True
    template_name = "bread/layout.html"

    def __init__(self, *args, **kwargs):
        self.fields = kwargs.get("fields", getattr(self, "fields", ["__all__"]))
        super().__init__(*args, **kwargs)

    def layout(self, request):
        return _layout.BaseElement(
            _layout.H3(
                pretty_modelname(self.model),
                " ",
                _layout.I(lambda c: c["object"]),
            ),
            [
                _layout.form.FormField(field, widgetattributes={"readonly": True})
                for field in filter_fieldlist(self.model, self.fields, for_form=True)
            ],
        )

    def field_values(self):
        for accessor in self.fields:
            fieldchain = resolve_relationship(self.model, accessor)
            if not fieldchain:
                yield accessor, accessor.replace("_", " ").title()
            else:
                yield accessor, pretty_fieldname(fieldchain[-1][1])

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.view_{self.model.__name__.lower()}"]
