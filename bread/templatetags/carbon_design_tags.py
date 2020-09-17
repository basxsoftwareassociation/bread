from django import template
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.forms.utils import flatatt

register = template.Library()


@register.simple_tag
def carbon_icon(name, size=32, **kwargs):
    flatattribs = flatatt(kwargs)
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
