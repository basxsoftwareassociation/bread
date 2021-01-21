import htmlgenerator as hg
from django.core.exceptions import FieldDoesNotExist
from django.utils import formats

from bread.utils import pretty_fieldname
from bread.utils.urls import reverse_model


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
        return getattr(getattr(model, field), "verbose_name", "")


class FormattedContextValue(hg.ContextValue):
    def resolve(self, context, element):
        return formats.localize(super().resolve(context, element))


FC = FormattedContextValue
