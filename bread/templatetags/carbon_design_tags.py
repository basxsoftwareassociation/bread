from django import template
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.forms.utils import flatatt
from django.template.loader import get_template

from pybars import Compiler

compiler = Compiler()

register = template.Library()


@register.simple_tag
def carbon_icon(name, **kwargs):
    """Insert the SVG for a carvon icon.
    See https://www.carbondesignsystem.com/guidelines/icons/library for a list of all icons.
    In order to see the name which should be passed to this template tag, click on "Download SVG" for an
    icon and use the filename without the attribte, e.g. "thunderstorm--severe"."""
    flatattribs = flatatt(kwargs)
    size = None
    if name[-2:].isdigit():
        size = int(name[-2:])
    key = f"icon_{name}__{size}__{flatattribs}".lower()
    if cache.get(key) is None:
        path = "design/carbon_design/icons/"
        if size:
            path += f"{size}/"
        path += "{name}.svg"
        svg = "".join(
            [
                l.replace("<svg", f"<svg {flatattribs}")
                for l in default_storage.open(path).readlines()
            ]
        )
        cache.set(key, svg)
        return svg
    return cache.get(key)


@register.simple_tag(takes_context=True)
def handlbars(context, template_name):
    template = compiler.compile(get_template(template_name).origin)
    return template(context)


@register.filter
def lookup(obj, attr):
    """Is used in order to make transpiling the hbs templates easier"""
    return getattr(obj, attr, None)
