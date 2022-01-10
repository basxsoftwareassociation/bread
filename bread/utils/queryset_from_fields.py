import django_countries
from django.db import models
from django.db.models import Q
from django_countries.fields import CountryField


def get_char_text_qset(fields, searchquery, prefix):
    char_text_fields = {
        f
        for f in fields
        if isinstance(f, models.fields.CharField)
        or isinstance(f, models.fields.TextField)
    }

    return {
        Q(**{prefix + "_".join((f.name, "_contains")): searchquery})
        for f in char_text_fields
    }


def get_country_qset(fields, searchquery, prefix):
    countries = {name.lower(): code for code, name in django_countries.countries}
    country_fields = {f for f in fields if isinstance(f, CountryField)}

    if not country_fields:
        return set()

    match_countries = {
        country_name for country_name in countries if searchquery in country_name
    }

    return {
        Q(**{prefix + f.name: countries[key]})
        for f in country_fields
        for key in match_countries
    }


def get_field_queryset(fields, searchquery, prefix="", follow_relationships=1):
    queryset = {
        *get_char_text_qset(fields, searchquery, prefix),
        *get_country_qset(fields, searchquery, prefix),
    }

    qs = Q()
    for query in queryset:
        qs |= query

    if follow_relationships > 0:
        foreignkey_fields = {
            f
            for f in fields
            if isinstance(f, models.fields.related.ForeignKey)
            or isinstance(f, models.fields.related.ManyToManyField)
        }
        for foreignkey_field in foreignkey_fields:
            # skip fields with a name beginning with '_'
            if foreignkey_field.name[0] == "_":
                continue

            if foreignkey_field.related_model:
                foreign_fields = foreignkey_field.related_model._meta.fields
            else:
                foreign_fields = foreignkey_field._meta.fields

            new_prefix = prefix + "__".join([foreignkey_field.name, ""])
            qs |= get_field_queryset(
                foreign_fields, searchquery, new_prefix, follow_relationships - 1
            )

    return qs
