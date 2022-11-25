import datetime

import htmlgenerator as hg
from django.conf import settings
from django.db import models
from django.db.models import ManyToOneRel
from django.db.models.fields.related_descriptors import ReverseManyToOneDescriptor
from django.template.defaultfilters import linebreaksbr
from django.utils.formats import localize as djangolocalize
from django.utils.text import slugify as djangoslufigy
from django.utils.timezone import localtime as djangolocaltime

from ..formatters import as_download
from ..utils import resolve_modellookup

DEVMODE_KEY = "DEVMODE"


class HasBasxBreadCookieValue(hg.Lazy):
    def __init__(self, cookiename, value, default=None):
        self.cookiename = cookiename
        self.value = value
        self.default = default

    def resolve(self, context):
        if f"basxbread-{self.cookiename}" in context["request"].session.get(
            "basxbread-cookies", {}
        ):
            return (
                context["request"].session["basxbread-cookies"][
                    f"basxbread-{self.cookiename}"
                ]
                == self.value
            )
        return self.default == self.value


class DevModeOnly(hg.BaseElement):
    def render(self, context, stringify=True, fragment=None):
        if context["request"].session.get(DEVMODE_KEY, False):
            return super().render(context, stringify=stringify, fragment=fragment)
        return ""


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
        label = getattr(
            object._meta.model.objects.get_queryset().query.annotations.get(
                self.fieldname, None
            ),
            "output_field",
            label,
        )  # test for annotated ("dynamic") fields

        if isinstance(label, ReverseManyToOneDescriptor):
            label = label.rel.field.remote_field

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

        if isinstance(value, models.fields.files.FieldFile) and not self.formatter:
            return as_download(value)

        if isinstance(value, datetime.datetime):
            value = djangolocaltime(value)

        if self.formatter:
            value = self.formatter(value)

        if isinstance(value, (type(None), bool)):
            value = {
                True: settings.HTML_TRUE,
                False: settings.HTML_FALSE,
                None: settings.HTML_NONE,
            }[value]

        value = djangolocalize(value, use_l10n=settings.USE_L10N)
        if isinstance(value, models.Manager):
            value = ", ".join([str(x) for x in value.all()])
        if isinstance(value, str):
            value = linebreaksbr(value)
        return value


localize = hg.lazify(djangolocalize)
localtime = hg.lazify(djangolocaltime)
slugify = hg.lazify(djangoslufigy)
