from bread import menu as menuregister
from django import template
from django.db import models

from ..admin import site
from ..formatters import format_value
from ..utils import has_permission, pretty_fieldname, title

register = template.Library()

register.simple_tag(pretty_fieldname)
register.simple_tag(has_permission)
register.filter(format_value)


# tags
@register.simple_tag
def pretty_modelname(model, plural=False):
    if plural:
        return title(model._meta.verbose_name_plural)
    return title(model._meta.verbose_name)


@register.simple_tag
def adminurl(model, urlname, *args, **kwargs):
    return site.get_default_admin(model).reverse(urlname, *args, **kwargs)


@register.simple_tag
def render_field(admin, object, fieldname):
    return admin.render_field(object, fieldname)


@register.simple_tag
def render_field_aggregation(admin, queryset, fieldname):
    return admin.render_field_aggregation(queryset, fieldname)


@register.simple_tag
def object_actions(admin, request, object):
    return admin.object_actions(request, object)


@register.simple_tag
def list_actions(admin, request):
    return admin.list_actions(request)


@register.simple_tag
def add_action(admin, request):
    return admin.add_action(request)


@register.simple_tag
def pagename(request):
    return " / ".join(
        [
            title(namespace.replace("_", " "))
            for namespace in request.resolver_match.namespaces
        ]
    )


@register.simple_tag
def querystring_order(admin, current_order, fieldname):
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
    """Take the current GET query and update/add an item"""
    current_query = context["request"].GET.copy()
    current_query[key] = value
    return context["request"].path + "?" + current_query.urlencode()


# filters


@register.filter
def is_external_url(url):
    """Return ``True`` if the url is linked to an external page"""
    return url.startswith("http")


@register.filter
def to_underscore(string):
    """Return string with dash (-) replaced with underscore (_)"""
    return string.replace("-", "_")


@register.simple_tag
def menu(request):
    """
    returns nested iterables:
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
    user = request.user
    menugroups = []
    has_active_menu = False
    for group in sorted(menuregister.main._registry.values()):
        if group.has_permission(user):
            has_active_menu = has_active_menu or group.active(request)
            menugroups.append(
                [
                    group.label,
                    group.active(request),
                    (
                        (item.label, item.active(request), item.get_url(request))
                        for item in sorted(group.items)
                        if item.has_permission(user)
                    ),
                ]
            )
    if not has_active_menu:
        for group in menugroups:
            if menuregister.main._registry[group[0]].active_in_current_app(request):
                group[1] = True
                break
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
            if isinstance(related_objects, models.Model):
                ret.append([related_objects])
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
            if isinstance(related_objects, models.Model):
                ret.append([related_objects])
            elif related_objects.exists():
                ret.append(related_objects.all())
    return ret
