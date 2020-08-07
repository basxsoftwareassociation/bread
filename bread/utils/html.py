from django.utils.html import mark_safe
from django.utils.text import format_lazy


def tagwrapper(html, style={}, classes=[], attrs={}, tag="div"):
    if classes:
        attrs["class"] = classes
    if style:
        attrs["style"] = style

    attr_formatted = {}
    for attrname, attrvalue in attrs.items():
        if isinstance(attrvalue, list):
            attrvalue = " ".join(attrvalue)
        elif isinstance(
            attrvalue, dict
        ):  # maybe this is only used for styles? better solution?
            attrvalue = "; ".join([f"{k}: {v}" for k, v in attrvalue.items()])
        attr_formatted[attrname] = attrvalue

    attr_string = " ".join([f'{k}="{v}"' for k, v in attr_formatted.items()])

    return mark_safe(
        format_lazy(
            "<{tag} {attrs}>{html}</{tag}>", tag=tag, html=html, attrs=attr_string
        )
    )
