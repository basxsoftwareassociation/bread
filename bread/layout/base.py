import htmlgenerator as hg

from bread.utils import pretty_modelname
from bread.utils.urls import reverse_model

from ..formatters import format_value


def fieldlabel(model, accessor):
    field = hg.resolve_lookup(model, accessor)
    try:
        return field.verbose_name  # manualy set
    except AttributeError:
        try:
            return field.field.verbose_name  # model field
        except AttributeError:
            try:
                return field.__name__  # method
            except AttributeError:
                try:
                    return field.fget.__name__  # property
                except AttributeError:
                    return field


def objectaction(object, action, *args, **kwargs):
    kwargs["kwargs"] = {"pk": object.pk}
    return str(
        reverse_model(
            object,
            action,
            *args,
            **kwargs,
        )
    )


def aslink_attributes(href):
    """
    Shortcut to generate HTMLElement attributes to make any element behave like a link.
    This should normally be used like this: hg.DIV("hello", \\*\\*aslink_attributes('google.com'))
    """
    return {
        "onclick": hg.BaseElement("document.location = '", href, "'"),
        "onauxclick": hg.BaseElement("window.open('", href, "', '_blank')"),
        "style": "cursor: pointer",
    }


class ModelName(hg.ContextValue):
    def resolve(self, context, element):
        return pretty_modelname(super().resolve(context, element))


class FormattedContextValue(hg.ContextValue):
    def resolve(self, context, element):
        value = super().resolve(context, element)
        return format_value(value)


FC = FormattedContextValue
