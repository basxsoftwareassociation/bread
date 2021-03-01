import htmlgenerator as hg
from django.core.exceptions import FieldDoesNotExist

from bread.utils import pretty_modelname
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


class ModelName(hg.ContextValue):
    def resolve(self, context, element):
        return pretty_modelname(super().resolve(context, element))


def fieldlabel(model, accessor):
    try:
        # if the accessor starts with access to a field we would only get the DeferredAttribute
        # from django, therefore we need to insert a "field" attribute accessor
        first = accessor.split(".")[0]
        model._meta.get_field(first)
        accessor = ".".join([first, "field"] + accessor.split(".")[1:])
    except FieldDoesNotExist:
        pass
    label = hg.resolve_lookup(model, accessor, call_functions=False)
    return getattr(label, "verbose_name", label)


class FormattedContextValue(hg.ContextValue):
    def resolve(self, context, element):
        value = super().resolve(context, element)
        return format_value(value)


FC = FormattedContextValue
