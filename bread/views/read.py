import copy

from crispy_forms.layout import Layout
from guardian.mixins import PermissionRequiredMixin

from django.views.generic import DetailView

from ..layout import convert_to_formless_layout
from ..layout.components import plisplate
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
        if not isinstance(layout, plisplate.BaseElement):
            layout = [
                plisplate.form.FormField(field, widgetattributes={"readonly": True})
                for field in filter_fieldlist(self.model, layout, for_form=True)
            ]
        self.layout = plisplate.BaseElement(
            plisplate.H2(
                self.admin.verbose_modelname, " ", plisplate.I(lambda c: c["object"]),
            ),
            layout,
        )

        super().__init__(*args, **kwargs)

    def get_layout(self, request, fields_argument):
        """fields_argument is anything that has been passed as ``fields`` to the as_view function"""
        # need a deep copy because convert_to_formless_layout will modify the value
        # which is problematic if we share the same layout-object with an edit view

        fields_argument = copy.deepcopy(fields_argument)
        if not isinstance(fields_argument, Layout):
            layoutfields = filter_fieldlist(self.model, fields_argument)
            fields_argument = Layout(*layoutfields)
        convert_to_formless_layout(fields_argument)
        return fields_argument

    def field_values(self):
        for accessor in self.fields:
            fieldchain = resolve_relationship(self.model, accessor)
            if not fieldchain:
                yield accessor, accessor.replace("_", " ").title()
            else:
                yield accessor, pretty_fieldname(fieldchain[-1][1])

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.view_{self.model.__name__.lower()}"]
