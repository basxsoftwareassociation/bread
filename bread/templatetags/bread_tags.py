import ckeditor
from bread import menu as menuregister
from django import forms, template
from django.conf import settings
from django.db import models
from django.template.loader import render_to_string

from ..admin import site
from ..formatters import format_value
from ..utils import has_permission, pretty_fieldname

register = template.Library()

register.simple_tag(pretty_fieldname)
register.simple_tag(has_permission)
register.filter(format_value)


@register.simple_tag
def pretty_modelname(model, plural=False):
    if plural:
        return model._meta.verbose_name_plural.title()
    return model._meta.verbose_name.title()


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
def pagename(request):
    return " / ".join(
        [
            namespace.replace("_", " ").title()
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


@register.filter
def is_external_url(url):
    """Return ``True`` if the url is linked to an external page"""
    return url.startswith("http")


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


@register.filter
def materializecss(element):
    """Filter to print an element in materializecss style
    Just adds some materialcss classes to the input widgets and renders ``bread/form.html``
    """
    if isinstance(element, forms.fields.BoundField):
        if isinstance(element.field.widget, forms.CheckboxInput):
            return render_to_string("bread/fields/checkbox.html", {"field": element})
        elif isinstance(element.field.widget, ckeditor.widgets.CKEditorWidget):
            return render_to_string("bread/fields/ckeditor.html", {"field": element})
        elif isinstance(element.field.widget, forms.FileInput):
            return render_to_string("bread/fields/file.html", {"field": element})
        elif isinstance(element.field.widget, forms.Select) and len(
            element.field.widget.choices
        ) > getattr(settings, "AUTOCOMPLETE_IF_MORE_THAN", 7):
            element.field.widget.attrs.update({"class": "no-autoinit"})
            element.field.empty_label = ""
            return render_to_string(
                "bread/fields/autocomplete.html", {"field": element}
            )
        else:
            prepare_widget(element.field.widget, element.field, element.errors)
            return render_to_string("bread/fields/wrapper.html", {"field": element})

    return render_to_string("bread/form.html", {"form": element})


def prepare_widget(widget, field, has_error):
    """
    Adds classes and makes changes to the widget in order to be materialize compatible
    Sometimes information from the form field is necessary, therefore the field parameter
    If we have a MultiWidget, widget != field.widget
    """

    unstyled_widgets = [
        forms.CheckboxSelectMultiple,
        forms.RadioSelect,
        forms.FileInput,
    ]
    # TODO: handle subwidgets
    if isinstance(widget, forms.MultiWidget):
        for subwidget in widget.widgets:
            prepare_widget(subwidget, field, has_error)

    # TODO: Bug with materializecss, select will not use html5-required attribute
    # does not affect form submitssion
    if isinstance(widget, forms.Select) or isinstance(widget, forms.SelectMultiple):
        field.required = False

    if isinstance(widget, forms.DateInput):
        widget.attrs.update({"class": "datepicker"})

    if isinstance(widget, forms.TimeInput):
        widget.attrs.update({"class": "timepicker"})

    # Textareas are often used for more special things like WYSIWYG editors and therefore
    # we only apply materialize if this is a direct instance, not inherited
    if type(field) == forms.fields.CharField and type(field.widget) == forms.Textarea:
        widget.attrs.update({"class": "materialize-textarea"})

    if not any([isinstance(widget, fieldtype) for fieldtype in unstyled_widgets]):
        classes = widget.attrs.get("class", "")
        classes += " validate"
        if has_error:
            classes += " invalid"
        widget.attrs["class"] = classes


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
            if related_objects.exists():
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
            if related_objects.exists():
                ret.append(related_objects.all())
    return ret
