import logging
import warnings

import htmlgenerator as hg
from _strptime import TimeRE
from django import template
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.utils import formats
from django.utils.html import mark_safe

from .. import layout as layout
from .. import menu as menuregister
from ..formatters import as_object_link, format_value
from ..utils import has_permission, pretty_fieldname

logger = logging.getLogger(__name__)
register = template.Library()

register.simple_tag(pretty_fieldname)
register.simple_tag(has_permission)
register.filter(format_value)


# tags


@register.simple_tag
def dateformatstr2regex(formatstr, format_key):
    formatstr = formatstr or formats.get_format(format_key)[0]
    return TimeRE().compile(formatstr).pattern


@register.simple_tag
def linkpermission(link, request, obj=None):
    return link.has_permission(request, obj)


@register.simple_tag(takes_context=True)
def linkurl(context, link):
    return link.url


@register.simple_tag
def display_link(link, request, obj=None, atag_class="", atag_style=""):
    warnings.warn(
        "the template tag display_link is deprecated, please use the tags linkpermission and linkurl"
    )

    ret = ""
    if link.has_permission(request, obj):
        url = link.url
        target = (
            'target="_blank" rel="noopener noreferrer"'
            if url.startswith("http")
            else ""
        )
        ret += f'<a href="{url}" class="{atag_class}" style="{atag_style}" {target}>'
        if link.icon is not None:
            ret += f'<i class="material-icons" style="vertical-align:middle">{link.icon}</i> '
        if link.label is not None:
            ret += link.label
        ret += "</a>"
    return mark_safe(ret)


@register.simple_tag
def has_link_permission(link, request, obj=None):
    return link.has_permission(request, obj)


@register.simple_tag
def pagename(request):
    return " / ".join(
        [
            namespace.replace("_", " ").title()
            for namespace in request.resolver_match.namespaces
        ]
    )


@register.simple_tag(takes_context=True)
def object_link(context, instance, label=None):
    return as_object_link(instance, label)


@register.simple_tag
def querystring_order(current_order, fieldname):
    """Return order fields according to the current GET-parameters but change the order-parameter of the given field"""
    fieldname_rev = "-" + fieldname
    ordering = current_order.split(",")
    if fieldname in ordering:
        ordering.remove(fieldname)
        ordering.insert(0, fieldname_rev)
    elif fieldname_rev in ordering:
        ordering.remove(fieldname_rev)
    else:
        ordering.insert(0, fieldname)
    return ",".join(filter(None, ordering))


@register.simple_tag(takes_context=True)
def updated_querystring(context, key, value):
    """Take the current GET query and update/add an entry"""
    current_query = context["request"].GET.copy()
    current_query[key] = value
    return context["request"].path + "?" + current_query.urlencode()


# filters


@register.simple_tag
def menu(request):
    """
    Returns nested iterables::

        [
            [group, active, (
                (item, active, url),
                (item, active, url),
            )],
            [group, active, (
                (item, active, url),
                (item, active, url),
            )]
        ]

    If no menu group is active will try to find active menu by comparing labels to current appname
    """
    menugroups = []
    has_active_menu = False
    for group in sorted(menuregister.main._registry.values()):
        if group.has_permission(request):
            has_active_menu = has_active_menu or group.active(request)
            menugroups.append(
                [
                    group.label,
                    group.icon,
                    group.active(request),
                    [
                        (item, item.active(request), item.link.url)
                        for item in sorted(group.items)
                        if item.has_permission(request)
                    ],
                ]
            )
    # Does not work with translation
    # if not has_active_menu:
    # for group in menugroups:
    # if menuregister.main._registry[group[0]].active_in_current_app(request):
    # group[1] = True
    # break
    return menugroups


# TODO: check recursively?
@register.simple_tag
def list_delete_cascade(object):
    ret = []
    for field in object._meta.get_fields():
        if (
            hasattr(field, "on_delete")
            and field.on_delete == models.CASCADE
            and hasattr(object, field.get_accessor_name())
        ):
            related_objects = getattr(object, field.get_accessor_name())
            # hack so that we can always work with querysets
            if isinstance(related_objects, models.Model):
                ret.append(
                    related_objects._meta.model.objects.filter(id=related_objects.id)
                )
            elif related_objects.exists():
                ret.append(related_objects.all())
    return ret


# TODO: check recursively?
@register.simple_tag
def list_delete_protection(object):
    ret = []
    for field in object._meta.get_fields():
        if (
            hasattr(field, "on_delete")
            and field.on_delete == models.PROTECT
            and hasattr(object, field.get_accessor_name())
        ):
            related_objects = getattr(object, field.get_accessor_name())
            # hack so that we can always work with querysets
            if isinstance(related_objects, models.Model):
                ret.append(
                    related_objects._meta.model.objects.filter(id=related_objects.id)
                )
            elif related_objects.exists():
                ret.append(related_objects.all())
    return ret


# TODO: this should be removed in the future when we will only use htmlgenerator layouts
@register.simple_tag
def carbon_icon(name, size, **attributes):
    return mark_safe(hg.render(layout.icon.Icon(name, size, **attributes), {}))


@register.simple_tag
def display_messages(messages):
    notifications = []
    for i, message in enumerate(messages):
        kind = "info" if message.level_tag == "debug" else message.level_tag
        notifications.append(
            layout.notification.ToastNotification(
                message=message.tags.capitalize(),
                details=message.message,
                kind=kind,
                hidetimestamp=True,
                style=f"opacity: 0; animation: {4 + 3 * i}s ease-in-out notification",
                onload=f"setTimeout(() => this.style.display = 'None', {(4 + 3 * i) * 1000})",  # need to hide the element after animation is done
            )
        )
    return mark_safe(hg.render(hg.DIV(*notifications), {}))


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
        except FieldDoesNotExist:
            return ""
    return ""


def render_layout(parser, token):
    try:
        tag_name, layoutvariable = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires a single argument" % token.contents.split()[0]
        )
    return LayoutNode(layoutvariable)


class LayoutNode(template.Node):
    def __init__(self, layout_variable):
        self.layout_variable = template.Variable(layout_variable)

    def render(self, context):
        try:
            layout = self.layout_variable.resolve(context)
            return "".join(layout.render(context.flatten()))
        except template.VariableDoesNotExist:
            return ""


register.tag("render_layout", render_layout)
