from crispy_forms.layout import Div, Layout
from crispy_forms.utils import TEMPLATE_PACK
from django.forms.formsets import DELETION_FIELD_NAME

from .. import formatters
from ..utils import pretty_fieldname, title


class NonFormContent(Div):
    """Prevents components to contribute to the list of form fields"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields = []


class FieldLabel(NonFormContent):
    """Renders the verbose name of a field """

    def __init__(self, field, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field = field

    def render(self, form, form_style, context, template_pack=TEMPLATE_PACK, **kwargs):
        obj = context.get("object") or context["form"].instance
        if hasattr(obj, "_meta"):
            return pretty_fieldname(obj._meta.get_field(self.field))
        elif hasattr(getattr(obj, self.field), "verbose_name"):
            return title(getattr(obj, self.field).verbose_name)
        return title(self.field)


class ReadonlyField(NonFormContent):
    def __init__(self, field, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field = field

    def render(self, form, form_style, context, template_pack=TEMPLATE_PACK, **kwargs):
        obj = context.get("object") or context["form"].instance
        return formatters.render_field(obj, self.field)


class InlineLayout(Layout):
    def __init__(self, inlinefield, *args, **kwargs):
        super().__init__(inlinefield)
        self.fieldname = inlinefield
        self.args = args
        self.kwargs = kwargs

    def get_inline_layout(self):
        if (
            DELETION_FIELD_NAME not in self.args
            and DELETION_FIELD_NAME not in self.kwargs
        ):
            self.args = self.args + (DELETION_FIELD_NAME, "id")
        return Layout(*self.args, **self.kwargs)
