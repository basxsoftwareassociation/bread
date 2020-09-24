from crispy_forms.layout import Div, Layout
from crispy_forms.utils import TEMPLATE_PACK
from django.forms.formsets import DELETION_FIELD_NAME
from django.template.loader import render_to_string

from .. import FieldLabel, ReadonlyField


class Component(Div):
    template = None

    def render(self, form, form_style, context, template_pack=TEMPLATE_PACK, **kwargs):
        children = self.get_rendered_fields(
            form, form_style, context, template_pack, **kwargs
        )

        template = self.get_template_name(template_pack)
        return render_to_string(
            template, {"component": self, "children": children, **context.flatten()}
        )


def convert_to_formless_layout(layout_object):
    """Recursively convert fields of type string to ReadonlyField.
    Usefull if a layout has been defined for native crispy-form layouts
    and should be reused on a read-only view."""
    for i, field in enumerate(layout_object.fields):
        if isinstance(field, str):
            layout_object.fields[i] = Div(FieldLabel(field), ReadonlyField(field))
        elif hasattr(field, "fields"):
            convert_to_formless_layout(field)


class InlineLayout(Layout):
    def __init__(self, inlinefield, *args, **kwargs):
        super().__init__(inlinefield)
        self.fieldname = inlinefield
        self.wrapper = kwargs.pop("wrapper", Div())
        self.args = args
        self.kwargs = kwargs

    def get_wrapper_layout(self):
        return self.wrapper

    def get_inline_layout(self):
        if (
            DELETION_FIELD_NAME not in self.args
            and DELETION_FIELD_NAME not in self.kwargs
        ):
            self.args = self.args + (DELETION_FIELD_NAME, "id")
        return Layout(*self.args, **self.kwargs)
