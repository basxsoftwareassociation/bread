import htmlgenerator as hg
from django.core.exceptions import FieldDoesNotExist

from bread.utils import pretty_fieldname, pretty_modelname
from bread.utils.urls import reverse_model

from ..formatters import format_value


def objectaction(object, action, *args, **kwargs):
    return str(
        reverse_model(
            object,
            action,
            args=args,
            kwargs={
                **kwargs,
                "pk": object.pk,
            },
        )
    )


def aslink_attributes(href):
    """
    Shortcut to generate HTMLElement attributes to make any element behave like a link.
    This should normally be used like this: hg.DIV("hello", **aslink_attributes('google.com'))
    """
    return {
        "onclick": hg.BaseElement("document.location = '", href, "'"),
        "onauxclick": hg.BaseElement("window.open('", href, "', '_blank')"),
        "style": "cursor: pointer",
    }


def fieldlabel(model, field):
    try:
        return pretty_fieldname(model._meta.get_field(field))
    except FieldDoesNotExist:
        context = model
        for accessor in field.split("."):
            if hasattr(context, accessor):
                context = getattr(context, accessor)
            elif hasattr(context, "get"):
                context = context.get(accessor)

        if hasattr(context, "field"):
            return fieldlabel(context.field.model, context.field.name)
        if callable(context):
            return getattr(
                context, "verbose_name", context.__name__.replace("_", " ").title()
            )
        return getattr(context, "verbose_name", str(context))


class ModelName(hg.ContextValue):
    def resolve(self, context, element):
        return pretty_modelname(super().resolve(context, element))


class FieldLabel(hg.BaseElement):
    def __init__(self, model, fieldname):
        self.model = model
        self.fieldname = fieldname

    def render(self, context):
        model = hg.resolve_lazy(self.model, context, self)
        fieldname = hg.resolve_lazy(self.fieldname, context, self)
        if isinstance(fieldname, str):
            return fieldlabel(model, fieldname)
        return fieldname


class FormattedContextValue(hg.ContextValue):
    def resolve(self, context, element):
        value = super().resolve(context, element)
        return format_value(value)


FC = FormattedContextValue
