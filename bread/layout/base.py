from crispy_forms.layout import Div
from crispy_forms.utils import TEMPLATE_PACK
from django.core.exceptions import FieldDoesNotExist

from .. import formatters
from ..utils import pretty_fieldname, title


class NonFormField(Div):
    """Prevents components to contribute to the list of form fields"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields = []


class FieldLabel(NonFormField):
    """Renders the verbose name of a field """

    def __init__(self, field, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field = field

    def render(self, form, form_style, context, template_pack=TEMPLATE_PACK, **kwargs):
        obj = context.get("object") or context["form"].instance
        field = None
        if hasattr(obj, "_meta"):
            try:
                field = obj._meta.get_field(self.field)
            except FieldDoesNotExist:
                pass
        if field:
            return pretty_fieldname(obj._meta.get_field(self.field))
        elif hasattr(getattr(obj, self.field), "verbose_name"):
            return title(getattr(obj, self.field).verbose_name)
        return title(self.field.replace("_", " "))


class ReadonlyField(NonFormField):
    """Accepts an optional parameter ``renderer`` which will be called with the
    object and the field name when this field is beeing rendered"""

    def __init__(self, field, *args, **kwargs):
        self.renderer = kwargs.pop("renderer", formatters.render_field)
        super().__init__(*args, **kwargs)
        self.field = field

    def render(self, form, form_style, context, template_pack=TEMPLATE_PACK, **kwargs):
        obj = context.get("object") or context["form"].instance
        ret = str(self.renderer(obj, self.field))
        return ret
