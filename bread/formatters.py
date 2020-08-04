import datetime
import numbers
import random
from collections.abc import Iterable

from dateutil import tz
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.utils.html import format_html_join, linebreaks, mark_safe

import bread.settings as app_settings
from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField
from django_countries.fields import CountryField
from easy_thumbnails.files import get_thumbnailer

from .models import AccessConcreteInstanceMixin


def render_field(instance, fieldname, adminobject=None):
    if fieldname == "self":
        return as_object_link(instance, str(instance))

    while models.constants.LOOKUP_SEP in fieldname:
        accessor, fieldname = fieldname.split(models.constants.LOOKUP_SEP, 1)
        instance = getattr(instance, accessor, None)
        if isinstance(instance, models.Manager):
            rendered_fields = [
                render_field(o, fieldname, adminobject) for o in instance.all()
            ]
            return mark_safe(f"<ul><li>{'</li><li>'.join(rendered_fields)}</li></ul>")
    fieldtype = None
    try:
        fieldtype = instance._meta.get_field(fieldname)
    except FieldDoesNotExist:
        pass
    if hasattr(adminobject, fieldname):
        value = getattr(adminobject, fieldname)(instance)  # noqa
    elif hasattr(instance, f"get_{fieldname}_display") and not isinstance(
        fieldtype, CountryField
    ):
        value = getattr(instance, f"get_{fieldname}_display")()
    else:
        value = getattr(instance, fieldname, None)
    if callable(value) and not isinstance(value, models.Manager):
        value = value()
    return format_value(value, fieldtype)


def render_field_aggregation(queryset, fieldname, adminobject):
    DEFAULT_AGGREGATORS = {models.DurationField: models.Sum(fieldname)}
    modelfield = None
    try:
        modelfield = queryset.model._meta.get_field(fieldname)
        if isinstance(modelfield, GenericForeignKey):
            modelfield = None
    except FieldDoesNotExist:
        pass
    # check if there are aggrations defined on the breadadmin or on the model field
    aggregation_func = getattr(adminobject, f"{fieldname}_aggregation", None)
    if aggregation_func is None:
        aggregation_func = getattr(queryset.model, f"{fieldname}_aggregation", None)
    # if there is no custom aggregation defined but the field is a database fields, we just count distinct
    if aggregation_func is None:
        if type(modelfield) not in DEFAULT_AGGREGATORS:
            return ""
        aggregation = DEFAULT_AGGREGATORS[type(modelfield)]
    else:
        aggregation = aggregation_func(queryset)

    if isinstance(aggregation, models.Aggregate):
        return format_value(queryset.aggregate(value=aggregation)["value"], modelfield)
    return format_value(aggregation, modelfield)


def format_value(value, fieldtype=None):
    """Renders a python value in a nice way in HTML"""
    if isinstance(value, bool) or value is None:
        return CONSTANTS[value]

    # make referencing fields iterable (normaly RelatedManagers)
    if isinstance(value, models.Manager):
        value = value.all()

    # If there is a hint passed via fieldtype, use the accoring conversion function first (identity otherwise)
    # This is mostly helpfull for string-based fields like URLS, emails etc.
    value = MODELFIELD_FORMATING_HELPERS.get(type(fieldtype), lambda a: a)(value)

    if isinstance(value, bool) or value is None:
        return CONSTANTS[value]
    if isinstance(value, datetime.timedelta):
        return as_duration(value)
    if isinstance(value, datetime.datetime):
        return as_datetime(value)
    if isinstance(value, numbers.Number):
        return f"{value:f}".rstrip("0").rstrip(".")
    if isinstance(value, models.fields.files.ImageFieldFile):
        return as_image(value)
    if isinstance(value, models.fields.files.FieldFile):
        return as_download(value)
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        return as_list(value)
    if isinstance(value, models.Model):
        return as_object_link(value)
    return value


# Formatting functions: never pass None, always return string


def as_email(value):
    return mark_safe(f'<a href="mailto:{value}">{value}</a>')


def as_url(value):
    return mark_safe(
        f'<a href="{value}" target="_blank" rel="noopener noreferrer">{value}</a>'
    )


def as_text(value):
    text = linebreaks(value[:32])
    if len(value) > 32:
        modalid = int(random.random() * 100000000)
        text = f"""{text}... <a class="modal-trigger" href="#modal_{modalid}">Show</a>
        <div id="modal_{modalid}" class="modal modal-fixed-footer">
            <div class="modal-content">
                <p>{linebreaks(value)}</p>
            </div>
            <div class="modal-footer">
                <a href="#!" class="modal-close btn-flat">Close</a>
            </div>
        </div>
        """
    return mark_safe(text)


def as_time(value):
    if value.tzinfo:
        value = value.astimezone(tz.gettz(settings.TIME_ZONE))
    return f"{value.hour:02}:{value.minute:02}:{value.second:02}"


def as_duration(value):
    return str(value - datetime.timedelta(microseconds=value.microseconds))


def as_datetime(value):
    if value.tzinfo:
        value = value.astimezone(tz.gettz(settings.TIME_ZONE))

    return value.isoformat(sep=" ", timespec="seconds").rsplit("+", 1)[0]


def as_boolean(value):
    return mark_safe(
        f"<div class='center'>{app_settings.HTML_TRUE if value else app_settings.HTML_FALSE}</div>"
    )


def as_countries(value):
    return as_list((c.name for c in value))


def as_list(iterable):
    return (
        mark_safe("<ul>")
        + format_html_join("\n", "<li>{}</li>", ((format_value(v),) for v in iterable))
        + mark_safe("</ul>")
    )


def as_richtext(value):
    return mark_safe(value)


def as_download(value):
    if not value:
        return CONSTANTS[None]
    if not value.storage.exists(value.name):
        return mark_safe("<small><emph>File not found</emph></small>")
    return mark_safe(
        f'<a class="center" style="display: block" href="{value.url}"><i class="material-icons">open_in_browser</i></a>'
    )


def as_image(value):
    if not value:
        return CONSTANTS[None]
    if not value.storage.exists(value.name):
        return mark_safe("<small><emph>Image not found</emph></small>")
    im = get_thumbnailer(value).get_thumbnail({"size": (100, 100), "quality": 75})
    return mark_safe(
        f'<a class="center" style="display: block" href="{value.url}"><img src={im.url} width="{im.width}" height="{im.height}"/></a>'
    )


def as_audio(value):
    if not value:
        return CONSTANTS[None]
    if not value.storage.exists(value.name):
        return mark_safe("<small><emph>Audio file not found</emph></small>")
    return mark_safe(
        f"""
        <audio controls controlsList="nodownload" preload="metadata">
            <source src="{value.url}" type="audio/mp3">
        </audio>
    """
    )


def as_video(value):
    if not value:
        return CONSTANTS[None]
    if not value.storage.exists(value.name):
        return mark_safe("<small><emph>Video file not found</emph></small>")
    return mark_safe(
        f"""
        <video controls width="320" height="240" controlsList="nodownload" preload="metadata">
            <source src="{value.url}" type="video/mp4">
        </video>
    """
    )


def as_object_link(value, label=None):
    def get_link_from_admin(object):
        from .admin import site

        defaultadmin = site.get_default_admin(object)
        if defaultadmin is not None:
            return mark_safe(
                f'<a href="{defaultadmin.reverse("read", object.pk)}">{label or object}</a>'
            )

    if hasattr(value, "get_absolute_url"):
        return mark_safe(f'<a href="{value.get_absolute_url()}">{value}</a>')

    if (
        isinstance(value, AccessConcreteInstanceMixin) and value != value.concrete
    ):  # prevent endless recursion
        return as_object_link(value.concrete)
    return get_link_from_admin(value) or str(value)


# decorator wrappers to format functions outputs


def returns_email(func):
    return lambda *args, **kwargs: as_email(func(*args, **kwargs))


def returns_url(func):
    return lambda *args, **kwargs: as_url(func(*args, **kwargs))


def returns_text(func):
    return lambda *args, **kwargs: as_text(func(*args, **kwargs))


def returns_time(func):
    return lambda *args, **kwargs: as_time(func(*args, **kwargs))


def returns_duation(func):
    return lambda *args, **kwargs: as_duration(func(*args, **kwargs))


def returns_countries(func):
    return lambda *args, **kwargs: as_countries(func(*args, **kwargs))


def returns_list(func):
    return lambda *args, **kwargs: as_list(func(*args, **kwargs))


def returns_richtext(func):
    return lambda *args, **kwargs: as_richtext(func(*args, **kwargs))


def returns_download(func):
    return lambda *args, **kwargs: as_download(func(*args, **kwargs))


def returns_image(func):
    return lambda *args, **kwargs: as_image(func(*args, **kwargs))


def returns_object(func):
    return lambda *args, **kwargs: as_object_link(func(*args, **kwargs))


MODELFIELD_FORMATING_HELPERS = {
    None: lambda a: a,
    models.EmailField: as_email,
    models.ImageField: as_image,
    models.FileField: as_download,
    models.URLField: as_url,
    models.TextField: as_text,
    models.TimeField: as_time,
    models.DateTimeField: as_datetime,
    RichTextField: as_richtext,
    RichTextUploadingField: as_richtext,
    CountryField: as_countries,
}

CONSTANTS = {
    None: getattr(settings, "HTML_NONE", app_settings.HTML_NONE),
    True: getattr(settings, "HTML_TRUE", app_settings.HTML_TRUE),
    False: getattr(settings, "HTML_FALSE", app_settings.HTML_FALSE),
}
