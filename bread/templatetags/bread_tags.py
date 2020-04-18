import ckeditor
from bread import menu as menuregister
from bread.utils import (
    createurl,
    deleteurl,
    detailurl,
    has_permission,
    listurl,
    modelname,
    object_link,
    pretty_fieldname,
    updateurl,
)
from django import forms, template
from django.conf import settings
from django.db import models
from django.template.loader import render_to_string
from django.utils.http import urlencode

register = template.Library()

register.simple_tag(modelname)
register.simple_tag(pretty_fieldname)
register.simple_tag(listurl)
register.simple_tag(detailurl)
register.simple_tag(createurl)
register.simple_tag(updateurl)
register.simple_tag(deleteurl)
register.simple_tag(has_permission)
register.filter(object_link)


@register.simple_tag
def fieldsummary(model, field, queryset):
    """Render a summary of the given field over the given queryset"""
    return getattr(model, f"{field.name}_summary", lambda a: "")(queryset)


@register.filter
def display_field(object, field):
    """Render the given field of this object by calling object.get_{field.name}_display()"""
    return getattr(object, f"get_{field.name}_display", lambda: field)()


@register.filter
def underscore_to_space(value):
    return value.replace("_", " ")


@register.filter
def has_actions(object):
    """Check if the given object has custom actions defined (instead of edit and delete)"""
    return hasattr(object, "actions")


@register.filter
def has_additional_actions(object):
    """Check if the given object has any additional actions (adding to edit and delete)"""
    return hasattr(object, "additional_actions")


@register.simple_tag
def querystring_order(request, fieldname):
    """Return GET-parameters according to the current GET-parameters but change the order-parameter of the given field"""
    query = request.GET.copy()
    if query.get("order") == fieldname:
        query["order"] = "-" + fieldname
    elif query.get("order") == "-" + fieldname:
        query.pop("order")
    else:
        query["order"] = fieldname
    return query.urlencode()


@register.simple_tag
def add_next_url_parameter(url, request):
    """Adds a ``next`` url GET-parameter whose value is the current url

    :param url str: value of target (next) url
    :param request: current request object
    """
    concat = "&" if "?" in url else "?"
    return url + concat + urlencode({"next": request.get_full_path()})


@register.simple_tag
def urlparams(args):
    """Savely convert dict to url GET-parameters

    :param args dict: name-value mapping of url parameters
    """
    if not args:
        return ""
    safe_args = {k: v for k, v in args.items() if v is not None}
    if safe_args:
        return "?{}".format(urlencode(safe_args))
    return ""


@register.filter
def is_external_url(url):
    """Return ``True`` if the url is linked to an external page"""
    return url.startswith("http")


@register.simple_tag
def menu(request):
    """
    returns nested iterables:
    (
        (group, active, (
            (item, active, url),
            (item, active, url),
        )),
        (group, active, (
            (item, active, url),
            (item, active, url),
        ))
    )
    """
    user = request.user
    for group in sorted(menuregister.main.registry.values()):
        if group.has_permission(user):
            yield group.label, group.active(request), (
                (item.label, item.active(request), item.get_url())
                for item in sorted(group.items)
                if item.has_permission(user)
            )


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

    # Textarea are often used for more special things like WYSIWYG editors and therefore
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
