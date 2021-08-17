import datetime
import numbers
from collections.abc import Iterable

import htmlgenerator as hg
from dateutil import tz
from django.conf import settings
from django.db import models
from django.urls import NoReverseMatch
from django.utils.functional import Promise
from django.utils.html import format_html, format_html_join, linebreaks, mark_safe
from django_countries.fields import CountryField

import bread.settings as app_settings

from . import layout
from .utils.model_helpers import get_concrete_instance
from .utils.urls import reverse_model


def format_value(value, fieldtype=None):
    """Renders a python value in a nice way in HTML. If a field-definition has an attribute "renderer" set, that function will be used to render the value"""
    if hasattr(fieldtype, "renderer"):
        return fieldtype.renderer(value)

    if isinstance(value, bool) or value is None:
        return CONSTANTS[value]

    # make referencing fields iterable (normaly RelatedManagers)
    if isinstance(value, models.Manager):
        value = value.all()

    # If there is a hint passed via fieldtype, use the accoring conversion function first (identity otherwise)
    # This is mostly helpfull for string-based fields like URLS, emails etc.
    value = MODELFIELD_FORMATING_HELPERS.get(fieldtype.__class__, lambda a: a)(value)

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
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes, Promise)):
        return as_list(value)
    if isinstance(value, models.Model):
        try:
            return as_object_link(value)
        except NoReverseMatch:
            return value
    return value


# Formatting functions: never pass None, always return string


def as_email(value):
    return format_html('<a href="mailto:{}">{}</a>', value, value)


def as_url(value):
    return format_html(
        '<a href="{}" target="_blank" rel="noopener noreferrer">{}</a>', value, value
    )


def as_text(value):
    return mark_safe(linebreaks(value, autoescape=True))


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


def as_countries(value):
    return as_list((c.name for c in value))


def as_list(iterable, sep=", "):
    return format_html_join(sep, "{}", ((format_value(v),) for v in iterable))


def as_richtext(value):
    return mark_safe(value)


def as_download(value):
    if not value:
        return CONSTANTS[None]
    if not value.storage.exists(value.name):
        return mark_safe("<small><emph>File not found</emph></small>")
    return mark_safe(
        hg.render(
            hg.BaseElement(
                hg.A(
                    layout.icon.Icon("launch", size=16),
                    newtab=True,
                    href=value.url,
                    style="margin-right: 0.5rem; margin-left: 0.5rem",
                ),
                hg.A(
                    layout.icon.Icon("download", size=16), download=True, href=value.url
                ),
            ),
            {},
        )
    )


def as_image(value):
    if not value:
        return CONSTANTS[None]
    if not value.storage.exists(value.name):
        return mark_safe("<small><emph>Image not found</emph></small>")
    from easy_thumbnails.files import get_thumbnailer

    im = get_thumbnailer(value).get_thumbnail({"size": (100, 100), "quality": 75})
    return format_html(
        '<a class="center" href="{}"><img src={} width="{}" height="{}"/></a>',
        value.url,
        im.url,
        im.width,
        im.height,
    )


def as_audio(value):
    if not value:
        return CONSTANTS[None]
    if not value.storage.exists(value.name):
        return mark_safe("<small><emph>Audio file not found</emph></small>")
    return format_html(
        """
        <audio controls controlsList="nodownload" preload="metadata">
            <source src="{}" type="audio/mp3">
        </audio>
    """,
        value.url,
    )


def as_video(value):
    if not value:
        return CONSTANTS[None]
    if not value.storage.exists(value.name):
        return mark_safe("<small><emph>Video file not found</emph></small>")
    return format_html(
        """
        <video controls width="320" height="240" controlsList="nodownload" preload="metadata">
            <source src="{}" type="video/mp4">
        </video>
    """,
        value.url,
    )


def as_object_link(obj, label=None):
    if hasattr(obj, "get_absolute_url"):
        return format_html('<a href="{}">{}</a>', obj.get_absolute_url(), obj)

    return format_html(
        '<a href="{}">{}</a>',
        reverse_model(get_concrete_instance(obj), "read"),
        label or obj.__str__(),
    )


MODELFIELD_FORMATING_HELPERS = {
    None: lambda a: a,
    models.EmailField: as_email,
    models.ImageField: as_image,
    models.FileField: as_download,
    models.URLField: as_url,
    models.TextField: as_text,
    models.TimeField: as_time,
    models.DateTimeField: as_datetime,
    CountryField: as_countries,
}

CONSTANTS = {
    None: getattr(settings, "HTML_NONE", app_settings.HTML_NONE),
    True: getattr(settings, "HTML_TRUE", app_settings.HTML_TRUE),
    False: getattr(settings, "HTML_FALSE", app_settings.HTML_FALSE),
}
