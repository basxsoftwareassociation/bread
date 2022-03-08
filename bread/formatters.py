import datetime
import numbers
import os
from collections.abc import Iterable

import htmlgenerator as hg
from django.conf import settings
from django.db import models
from django.utils.functional import Promise
from django.utils.html import linebreaks, mark_safe
from django.utils.translation import gettext_lazy as _

import bread.settings as app_settings

from . import layout


def format_value(value):
    """
    Renders a python value in a nice way in HTML. If a field-definition has an
    attribute "renderer" set, that function will be used to render the value
    """
    if isinstance(value, bool) or value is None:
        return CONSTANTS[value]

    if isinstance(value, models.Manager):
        value = value.all()

    if isinstance(value, bool) or value is None:
        return CONSTANTS[value]
    if isinstance(value, datetime.timedelta):
        return as_duration(value)
    if isinstance(value, numbers.Number):
        return f"{float(value):f}".rstrip("0").rstrip(".")
    if isinstance(value, models.fields.files.FieldFile):
        return as_download(value)
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes, Promise)):
        return as_list(value)
    if isinstance(value, str):
        if "\n" in value:
            return as_text(value)
        if is_email_simple(value):
            return as_email(value)

    return value


# Formatting functions: never pass None, always return string


def as_email(value):
    return hg.A(value, href=hg.format("mailto: {}", value))


def as_url(value):
    return hg.A(value, href=value, target="_blank", rel="noopener noreferrer")


def as_text(value):
    return mark_safe(linebreaks(value, autoescape=True))


def as_duration(value):
    return str(value - datetime.timedelta(microseconds=value.microseconds))


def as_countries(value):
    return as_list((c.name for c in value))


def as_list(iterable):
    return hg.UL(hg.Iterator(iterable, "item", hg.LI(hg.C("item"))))


def as_download(value, label=None):
    if not value:
        return CONSTANTS[None]
    if not value.storage.exists(value.name):
        return hg.SMALL(hg.EM(_("File not found")))
    if label is None:
        label = hg.SPAN(os.path.basename(value.name))
    return hg.A(
        layout.icon.Icon(
            "launch",
            size=16,
            style="vertical-align: middle; margin-right: 0.25rem;",
        ),
        label,
        newtab=True,
        href=value.url,
        style="margin-right: 0.5rem; margin-left: 0.5rem",
        onclick="event.stopPropagation();",
    )


CONSTANTS = {
    None: getattr(settings, "HTML_NONE", app_settings.HTML_NONE),
    True: getattr(settings, "HTML_TRUE", app_settings.HTML_TRUE),
    False: getattr(settings, "HTML_FALSE", app_settings.HTML_FALSE),
}


# copied from
# https://github.com/django/django/blob/1f9874d4ca3e7376036646aedf6ac3060f22fd69/django/utils/html.py
# because older versions only have this as a local function available
def is_email_simple(value):
    """Return True if value looks like an email address."""
    # An @ must be in the middle of the value.
    if "@" not in value or value.startswith("@") or value.endswith("@"):
        return False
    try:
        p1, p2 = value.split("@")
    except ValueError:
        # value contains more than one @.
        return False
    # Dot must be in p2 (e.g. example.com)
    if "." not in p2 or p2.startswith("."):
        return False
    return True
