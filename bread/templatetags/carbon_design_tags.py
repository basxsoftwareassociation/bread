import logging
import re

from django import template
from django.contrib.staticfiles import finders
from django.core.cache import cache
from django.core.exceptions import FieldDoesNotExist
from django.forms.utils import flatatt
from django.utils.html import mark_safe

logger = logging.getLogger(__name__)
register = template.Library()


@register.simple_tag
def carbon_icon(name, size, **kwargs):
    """Insert the SVG for a carvon icon.
    See https://www.carbondesignsystem.com/guidelines/icons/library for a list of all icons.
    In order to see the name which should be passed to this template tag, click on "Download SVG" for an
    icon and use the filename without the attribte, e.g. "thunderstorm--severe"."""
    kwargs["width"] = size
    kwargs["height"] = size
    name = "--".join(_camel_case_split(name))
    flatattribs = flatatt(
        {k.replace("_", "-"): v for k, v in kwargs.items()}
    )  # replace is because of hbs to django template transpilation
    key = (
        f"icon_{name}__{size}__{flatattribs}".lower().replace('"', "").replace(" ", "_")
    )
    if cache.get(key) is None:
        path = finders.find(f"design/carbon_design/icons/32/{name.lower()}.svg")
        if not path:
            logger.error(f"Missing icon: {name.lower()}.svg")
            return f"Missing icon {name.lower()}.svg"
        with open(path) as f:
            svg = "".join(
                [l.replace("<svg", f"<svg {flatattribs}") for l in f.readlines()]
            )
        cache.set(key, svg)
        return mark_safe(svg)
    return mark_safe(cache.get(key))


def _camel_case_split(identifier):
    matches = re.finditer(
        ".+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)", identifier
    )
    return [m.group(0) for m in matches]


# The select element is a bit tricky to implement in a custom way because the options are
# only attached in the widgets context and are not easily available in the template.
# That means we leverage the default django rendering mechanism for the select but modify
# the widget to have all necessary classes
@register.filter
def make_select(field):
    """Used to add carbon classes to a select input"""
    field.field.widget.attrs["class"] = (
        field.field.widget.attrs.get("class", "") + " bx--select-input"
    )
    field.field.widget.template_name = "carbon_design/widgets/select.html"
    return field


@register.filter
def make_option(widget):
    """Used to add carbon classes to a select input"""
    widget["attrs"]["class"] = widget["attrs"].get("class", "") + " bx--select-option"
    return widget


@register.filter
def getplaceholder(field):
    if hasattr(field.field.widget, "placeholder"):
        return field.field.widget.placeholder
    if hasattr(field.field, "placeholder"):
        return field.field.placeholder
    if hasattr(field.form, "_meta"):
        try:
            return getattr(
                field.form._meta.model._meta.get_field(field.name), "placeholder", ""
            )
        except FieldDoesNotExists:
            return ""
    return ""
