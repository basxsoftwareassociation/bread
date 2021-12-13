from django.db import models
from django.db.models import Q
from django_countries import countries
from django_countries.fields import CountryField

# redefine the `countries` object to be a dict,
# with the key as a lowercase country names,
# and the corresponding values as country codes.
countries = {name.lower(): code for code, name in countries}


def get_char_text_qset(fields, queries):
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


def get_country_qset(fields, queries):
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


def get_queryset(fields, queries):
    queryset = {
        *get_char_text_qset(fields, queries),
        *get_country_qset(fields, queries),
    }

    foreignkey_fields = {
        f for f in fields if isinstance(f, models.fields.related.ForeignKey)
    }
    for foreignkey_field in foreignkey_fields:
        foreign_fields = foreignkey_field.related_model._meta.fields
        queryset |= {
            *get_char_text_qset(foreign_fields, queries),
            *get_country_qset(foreign_fields, queries),
        }

    qs = Q()
    for query in queryset:
        qs = qs | query

    return qs
