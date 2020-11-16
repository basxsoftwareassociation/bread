from guardian.mixins import PermissionRequiredMixin

from django.views.generic import DetailView

from .. import layout as _layout  # prevent name clashing
from ..utils import (
    CustomizableClass,
    filter_fieldlist,
    pretty_fieldname,
    resolve_relationship,
)


class ReadView(CustomizableClass, PermissionRequiredMixin, DetailView):
    admin = None
    fields = None
    accept_global_perms = True
    layout = None
    template_name = "carbon_design/dynamic_layout.html"

    def __init__(self, admin, *args, **kwargs):
        self.admin = admin
        self.model = admin.model
        layout = kwargs.get("layout", self.layout)
        if not isinstance(layout, _layout.BaseElement):
            layout = [
                _layout.form.FormField(field, widgetattributes={"readonly": True})
                for field in filter_fieldlist(self.model, layout, for_form=True)
            ]
        self.layout = _layout.BaseElement(
            _layout.H2(
                self.admin.verbose_modelname,
                " ",
                _layout.I(lambda c: c["object"]),
            ),
            layout,
        )

        super().__init__(*args, **kwargs)

    def get_layout(self):
        """fields_argument is anything that has been passed as ``fields`` to the as_view function"""
        return self.layout

    def field_values(self):
        for accessor in self.fields:
            fieldchain = resolve_relationship(self.model, accessor)
            if not fieldchain:
                yield accessor, accessor.replace("_", " ").title()
            else:
                yield accessor, pretty_fieldname(fieldchain[-1][1])

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.view_{self.model.__name__.lower()}"]
