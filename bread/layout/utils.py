import datetime

import htmlgenerator as hg
from django.conf import settings
from django.db import models
from django.db.models import ManyToOneRel
from django.template.defaultfilters import linebreaksbr
from django.utils.formats import localize
from django.utils.timezone import localtime
from django.utils.translation import gettext_lazy as _

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


def get_attribute_description_modal(obj):
    from . import datatable, modal

    columns = []
    fields = {f.name: f for f in obj._meta.get_fields()}
    for i in set(dir(obj) + list(vars(obj))):
        try:
            desc = _get_attribute_description(obj, i, fields)
            if desc is not None and desc[3]:
                f = desc[3]._meta.get_fields()
                additional_attrs = list(
                    filter(
                        None,
                        (
                            _get_attribute_description(desc[3], a, f)
                            for a in set(dir(desc[3]) + list(vars(desc[3])))
                        ),
                    )
                )
                desc = (
                    desc[0],
                    desc[1],
                    desc[2],
                    hg.BaseElement(
                        hg.UL(
                            hg.Iterator(
                                additional_attrs,
                                "attr",
                                hg.LI(
                                    hg.format("{}.{}", i, hg.C("attr.0")),
                                    style="font-weight: 700",
                                ),
                            )
                        ),
                    ),
                )
            if desc is not None:
                columns.append(desc)
        except Exception as e:
            columns.append((i, _("Unknown"), e))
    return modal.Modal(
        _("Available columns"),
        hg.DIV(
            hg.DIV(_("Bold text marks valid column names")),
            datatable.DataTable(
                columns=[
                    datatable.DataTableColumn(
                        _("Column name"),
                        hg.SPAN(hg.C("row.0"), style="font-weight: 700"),
                    ),
                    datatable.DataTableColumn(
                        _("Description"), hg.F(lambda c: c["row"][2])
                    ),
                    datatable.DataTableColumn(_("Type"), hg.F(lambda c: c["row"][1])),
                    datatable.DataTableColumn(_("Extended columns"), hg.C("row.3")),
                ],
                row_iterator=sorted(columns),
            ),
        ),
        size="lg",
    )


def _get_attribute_description(obj, attr, modelfields):
    # returns tuple(field_name, type_name, description, model)
    if attr.startswith("_"):  # leading underscore is "private" by convention in python
        return None
    if callable(getattr(obj, attr, None)):
        return None

    if attr in modelfields:
        if hasattr(modelfields[attr], "related_model") and getattr(
            modelfields[attr], "related_model"
        ):
            return (
                attr,
                f"{type(modelfields[attr]).__name__} -> "
                f"{modelfields[attr].related_model._meta.verbose_name}",
                getattr(modelfields[attr], "verbose_name", None),
                modelfields[attr].related_model,
            )
        else:
            return (
                attr,
                type(modelfields[attr]).__name__,
                modelfields[attr].verbose_name,
                None,
            )
    if hasattr(getattr(obj, attr, None), "related") and getattr(
        getattr(obj, attr, None), "related"
    ):
        return (
            attr,
            f"{type(getattr(obj, attr, None)).__name__} -> "
            f"{getattr(obj, attr, None).related.related_model._meta.verbose_name}",
            getattr(getattr(obj, attr, None), "verbose_name", None),
            getattr(obj, attr, None).related.related_model,
        )
    return (
        attr,
        type(getattr(obj, attr, None)).__name__,
        getattr(getattr(obj, attr, None), "verbose_name", None),
        None,
    )
