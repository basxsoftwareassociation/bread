import django_countries
from django.db import models
from django.db.models import Q
from django_countries.fields import CountryField


def get_char_text_qset(fields, queries, *args, **kwargs):
    char_text_fields = {
        f
        for f in fields
        if isinstance(f, models.fields.CharField)
        or isinstance(f, models.fields.TextField)
    }
    return {
        Q(**{"_".join((f.name, "_contains")): query})
        for f in char_text_fields
        for query in queries
    }


def get_country_qset(fields, queries, *args, **kwargs):
    countries = kwargs["countries"]  # for convenience of referencing.
    country_fields = {f for f in fields if isinstance(f, CountryField)}

    if not country_fields:
        return set()

    match_countries = {
        country_name
        for country_name in countries
        for query in queries
        if query.lower() in country_name
    }

    return {
        Q(**{f.name: countries[key]}) for f in country_fields for key in match_countries
    }


def get_field_queryset(fields, queries, *args, **kwargs):
    if "countries" not in kwargs:
        kwargs["countries"] = {
            name.lower(): code for code, name in django_countries.countries
        }

    queryset = {
        *get_char_text_qset(fields, queries, *args, **kwargs),
        *get_country_qset(fields, queries, *args, **kwargs),
    }

    qs = Q()
    for query in queryset:
        qs |= query

    foreignkey_fields = {
        f for f in fields if isinstance(f, models.fields.related.ForeignKey)
    }
    for foreignkey_field in foreignkey_fields:
        foreign_fields = foreignkey_field.related_model._meta.fields
        print(foreign_fields)
        qs |= get_field_queryset(fields, queries, *args, **kwargs)

    return qs
