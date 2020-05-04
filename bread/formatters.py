import datetime
import numbers
from collections.abc import Iterable

import bread.settings as app_settings
from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField
from django.conf import settings
from django.db import models
from django.utils.html import format_html_join, linebreaks, mark_safe
from django_countries.fields import CountryField
from sorl.thumbnail import get_thumbnail


def format_value(value, fieldtype=None):
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
    return mark_safe(linebreaks(value))


def as_duration(value):
    return mark_safe(":".join(str(value).split(":")[:3]))


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
    im = get_thumbnail(value, "100x100", crop="center", quality=75)
    return mark_safe(
        f'<a class="center" style="display: block" href="{value.url}"><img src={im.url} width="{im.width}" height="{im.height}"/></a>'
    )


def as_object_link(value):
    if hasattr(value, "get_absolute_url"):
        return f'<a href="{value.get_absolute_url()}">{value}</a>'
    return str(value)


# decorator wrappers to format functions outputs


def returns_email(func):
    return lambda *args, **kwargs: as_email(func(*args, **kwargs))


def returns_url(func):
    return lambda *args, **kwargs: as_url(func(*args, **kwargs))


def returns_text(func):
    return lambda *args, **kwargs: as_text(func(*args, **kwargs))


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
    RichTextField: as_richtext,
    RichTextUploadingField: as_richtext,
    CountryField: as_countries,
}

CONSTANTS = {
    None: getattr(settings, "HTML_NONE", app_settings.HTML_NONE),
    True: getattr(settings, "HTML_TRUE", app_settings.HTML_TRUE),
    False: getattr(settings, "HTML_FALSE", app_settings.HTML_FALSE),
}
