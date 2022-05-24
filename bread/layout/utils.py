import datetime

import htmlgenerator as hg
from django.conf import settings
from django.db import models
from django.db.models import ManyToOneRel
from django.template.defaultfilters import linebreaksbr
from django.utils.formats import localize
from django.utils.timezone import localtime

from ..formatters import format_value
from ..utils import pretty_modelname, resolve_modellookup, reverse_model

DEVMODE_KEY = "DEVMODE"


class HasBreadCookieValue(hg.Lazy):
    def __init__(self, cookiename, value, default=None):
        self.cookiename = cookiename
        self.value = value
        self.default = default

    def resolve(self, context):
        if f"bread-{self.cookiename}" in context["request"].session.get(
            "bread-cookies", {}
        ):
            return (
                context["request"].session["bread-cookies"][f"bread-{self.cookiename}"]
                == self.value
            )
        return self.default == self.value


class DevModeOnly(hg.BaseElement):
    def render(self, context):
        if context["request"].session.get(DEVMODE_KEY, False):
            return super().render(context)
        return ""


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
    def resolve(self, context):
        return pretty_modelname(super().resolve(context))


class FormattedContextValue(hg.ContextValue):
    def resolve(self, context):
        return str(format_value(super().resolve(context)))


class ObjectFieldLabel(hg.ContextValue):
    def __init__(self, fieldname, object_contextname="object", title=True):
        """
        :param fieldname: Name of the model field whose value will be rendered
        :param object_contextname: Name of the context object which provides the field value
                                   or a Lazy which produces the object itself
        """
        super().__init__(object_contextname)
        self.fieldname = fieldname
        self.title = title
        self.object = object_contextname

    def resolve(self, context):
        object = self.object
        if isinstance(self.object, str):
            object = resolve_modellookup(context, self.object)[0]
        object = hg.resolve_lazy(object, context)
        label = resolve_modellookup(object._meta.model, self.fieldname)[-1]
        if hasattr(label, "verbose_name"):
            return label.verbose_name
        if isinstance(label, property):
            return label.fget.__name__.replace("_", " ")
        if callable(label):
            return label.__name__.replace("_", " ")
        if isinstance(label, ManyToOneRel):
            return (
                label.related_model._meta.verbose_name_plural
            )  # this is "more correct", but not sure if it always works..
            # return label.name.replace("_", " ").capitalize()
        return label.title() if self.title and isinstance(label, str) else label


class ObjectFieldValue(hg.Lazy):
    def __init__(self, fieldname, object_contextname="object", formatter=None):
        """
        :param fieldname: Name of the model field whose value will be rendered
        :param object_contextname: Name of the context object which provides the field value
                                   or a Lazy which produces the object itself
        :param formatter: function which takes the field value as a single
                          argument and returns a formatted version
        """
        self.object = object_contextname
        self.fieldname = fieldname
        self.formatter = formatter

    def resolve(self, context):
        object = self.object
        if isinstance(self.object, str):
            object = resolve_modellookup(context, self.object)[0]
        object = hg.resolve_lazy(object, context)

        parts = self.fieldname.split(".")
        # test if the value has a matching get_FIELDNAME_display function
        try:
            value = hg.resolve_lookup(
                object, f"{'.'.join(parts[:-1])}.get_{parts[-1]}_display".lstrip(".")
            )
        except Exception:
            value = None
        if value is None:
            try:
                value = hg.resolve_lookup(object, self.fieldname)
            except AttributeError:
                # e.g. for non-existing OneToOneField related value
                pass
        if isinstance(value, datetime.datetime):
            value = localtime(value)
        if self.formatter:
            value = self.formatter(value)
        value = localize(value, use_l10n=settings.USE_L10N)
        if isinstance(value, models.Manager):
            value = ", ".join([str(x) for x in value.all()])
        if isinstance(value, str):
            value = linebreaksbr(value)
        return value


FC = FormattedContextValue
