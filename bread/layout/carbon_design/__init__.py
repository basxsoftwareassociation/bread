from crispy_forms.layout import Div, Layout
from crispy_forms.utils import TEMPLATE_PACK
from django.forms.formsets import DELETION_FIELD_NAME
from django.template import Template
from django.template.loader import render_to_string

from .. import HTMLTag


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


class InlineLayout(Layout):
    """Used to render inline forms"""

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


class ObjectActionsDropDown(HTMLTag):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field = ""
        self.fields = []
        self.template = Template("""Hi""")

    def render(self, form, form_style, context, template_pack=TEMPLATE_PACK, **kwargs):
        return self.template.render(context)
