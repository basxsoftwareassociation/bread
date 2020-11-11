import copy

from crispy_forms.layout import Layout
from django.views.generic import DetailView
from guardian.mixins import PermissionRequiredMixin

from ..layout import FieldValue, convert_to_formless_layout
from ..utils import (
    CustomizableClass,
    filter_fieldlist,
    get_modelfields,
    pretty_fieldname,
    resolve_relationship,
)


class ReadView(CustomizableClass, PermissionRequiredMixin, DetailView):
    template_name = "carbon_desgin/detail.html"
    admin = None
    fields = None
    sidebarfields = []
    accept_global_perms = True

    def __init__(self, admin, *args, **kwargs):
        self.admin = admin
        self.model = admin.model
        self.fields_argument = copy.deepcopy(kwargs.get("fields", self.fields))

        self.sidebarfields = get_modelfields(
            self.model, kwargs.get("sidebarfields", self.sidebarfields)
        )
        super().__init__(*args, **kwargs)

    def setup(self, request, *args, **kwargs):
        self.layout = self.get_layout(request, self.fields_argument)
        self.fields = self.get_fields(self.layout)
        return super().setup(request, *args, **kwargs)

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

    def get_fields(self, layout):
        def _get_fields_recursive(l):
            if isinstance(l, FieldValue):
                yield l.field
            else:
                for field in getattr(l, "fields", ()):
                    yield from _get_fields_recursive(field)

        return list(_get_fields_recursive(layout))

    def field_values(self):
        for accessor in self.fields:
            fieldchain = resolve_relationship(self.model, accessor)
            if not fieldchain:
                yield accessor, accessor.replace("_", " ").title()
            else:
                yield accessor, pretty_fieldname(fieldchain[-1][1])

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.view_{self.model.__name__.lower()}"]
