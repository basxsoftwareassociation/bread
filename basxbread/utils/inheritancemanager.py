# this is copied from https://github.com/jazzband/django-model-utils/blob/master/model_utils/managers.py
# Included to prevent having the whole package as dependency
# In case we encounter bugs or django API changes I recommend we fix them directly here
# by sam@basx.dev

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.constants import LOOKUP_SEP
from django.db.models.fields.related import OneToOneField, OneToOneRel
from django.db.models.query import ModelIterable, QuerySet


class InheritanceIterable(ModelIterable):
    def __iter__(self):
        queryset = self.queryset
        iter = ModelIterable(queryset)
        if getattr(queryset, "subclasses", False):
            extras = tuple(queryset.query.extra.keys())
            # sort the subclass names longest first,
            # so with 'a' and 'a__b' it goes as deep as possible
            subclasses = sorted(queryset.subclasses, key=len, reverse=True)
            for obj in iter:
                sub_obj = None
                for s in subclasses:
                    sub_obj = queryset._get_sub_obj_recurse(obj, s)
                    if sub_obj:
                        break
                if not sub_obj:
                    sub_obj = obj

                if getattr(queryset, "_annotated", False):
                    for k in queryset._annotated:
                        setattr(sub_obj, k, getattr(obj, k))

                for k in extras:
                    setattr(sub_obj, k, getattr(obj, k))

                yield sub_obj
        else:
            yield from iter


class InheritanceQuerySetMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._iterable_class = InheritanceIterable

    def select_subclasses(self, *subclasses):
        levels = None
        calculated_subclasses = self._get_subclasses_recurse(self.model, levels=levels)
        # if none were passed in, we can just short circuit and select all
        if not subclasses:
            subclasses = calculated_subclasses
        else:
            verified_subclasses = []
            for subclass in subclasses:
                # special case for passing in the same model as the queryset
                # is bound against. Rather than raise an error later, we know
                # we can allow this through.
                if subclass is self.model:
                    continue

                if not isinstance(subclass, (str,)):
                    subclass = self._get_ancestors_path(subclass, levels=levels)

                if subclass in calculated_subclasses:
                    verified_subclasses.append(subclass)
                else:
                    raise ValueError(
                        "{!r} is not in the discovered subclasses, tried: {}".format(
                            subclass, ", ".join(calculated_subclasses)
                        )
                    )
            subclasses = verified_subclasses

        # workaround https://code.djangoproject.com/ticket/16855
        previous_select_related = self.query.select_related
        if subclasses:
            new_qs = self.select_related(*subclasses)
        else:
            new_qs = self
        previous_is_dict = isinstance(previous_select_related, dict)
        new_is_dict = isinstance(new_qs.query.select_related, dict)
        if previous_is_dict and new_is_dict:
            new_qs.query.select_related.update(previous_select_related)
        new_qs.subclasses = subclasses
        return new_qs

    def _chain(self, **kwargs):
        update = {}
        for name in ["subclasses", "_annotated"]:
            if hasattr(self, name):
                update[name] = getattr(self, name)

        chained = super()._chain(**kwargs)
        chained.__dict__.update(update)
        return chained

    def _clone(self, klass=None, setup=False, **kwargs):
        qs = super()._clone()
        for name in ["subclasses", "_annotated"]:
            if hasattr(self, name):
                setattr(qs, name, getattr(self, name))
        return qs

    def annotate(self, *args, **kwargs):
        qset = super().annotate(*args, **kwargs)
        qset._annotated = [a.default_alias for a in args] + list(kwargs.keys())
        return qset

    def _get_subclasses_recurse(self, model, levels=None):
        """
        Given a Model class, find all related objects, exploring children
        recursively, returning a `list` of strings representing the
        relations for select_related
        """
        related_objects = [
            f for f in model._meta.get_fields() if isinstance(f, OneToOneRel)
        ]

        rels = [
            rel
            for rel in related_objects
            if isinstance(rel.field, OneToOneField)
            and issubclass(rel.field.model, model)
            and model is not rel.field.model
            and rel.parent_link
        ]

        subclasses = []
        if levels:
            levels -= 1
        for rel in rels:
            if levels or levels is None:
                for subclass in self._get_subclasses_recurse(
                    rel.field.model, levels=levels
                ):
                    subclasses.append(rel.get_accessor_name() + LOOKUP_SEP + subclass)
            subclasses.append(rel.get_accessor_name())
        return subclasses

    def _get_ancestors_path(self, model, levels=None):
        """
        Serves as an opposite to _get_subclasses_recurse, instead walking from
        the Model class up the Model's ancestry and constructing the desired
        select_related string backwards.
        """
        if not issubclass(model, self.model):
            raise ValueError("{!r} is not a subclass of {!r}".format(model, self.model))

        ancestry = []
        # should be a OneToOneField or None
        parent_link = model._meta.get_ancestor_link(self.model)
        if levels:
            levels -= 1
        while parent_link is not None:
            related = parent_link.remote_field
            ancestry.insert(0, related.get_accessor_name())
            if levels or levels is None:
                parent_model = related.model
                parent_link = parent_model._meta.get_ancestor_link(self.model)
            else:
                parent_link = None
        return LOOKUP_SEP.join(ancestry)

    def _get_sub_obj_recurse(self, obj, s):
        rel, _, s = s.partition(LOOKUP_SEP)

        try:
            node = getattr(obj, rel)
        except ObjectDoesNotExist:
            return None
        if s:
            child = self._get_sub_obj_recurse(node, s)
            return child
        else:
            return node

    def get_subclass(self, *args, **kwargs):
        return self.select_subclasses().get(*args, **kwargs)


class InheritanceQuerySet(InheritanceQuerySetMixin, QuerySet):
    def instance_of(self, *models):
        """
        Fetch only objects that are instances of the provided model(s).
        """
        # If we aren't already selecting the subclasess, we need
        # to in order to get this to work.

        # How can we tell if we are not selecting subclasses?

        # Is it safe to just apply .select_subclasses(*models)?

        # Due to https://code.djangoproject.com/ticket/16572, we
        # can't really do this for anything other than children (ie,
        # no grandchildren+).
        where_queries = []
        for model in models:
            where_queries.append(
                "("
                + " AND ".join(
                    [
                        '"{}"."{}" IS NOT NULL'.format(
                            model._meta.db_table,
                            field.attname,  # Should this be something else?
                        )
                        for field in model._meta.parents.values()
                    ]
                )
                + ")"
            )

        # the following line triggers a bandit SQL-injection error
        # however, the generated SQL does not consider any user input
        # and is generated soley from values from model._meta
        return self.select_subclasses(*models).extra(  # nosec
            where=[" OR ".join(where_queries)]
        )


class InheritanceManagerMixin:
    _queryset_class = InheritanceQuerySet

    def get_queryset(self):
        return self._queryset_class(self.model)

    def select_subclasses(self, *subclasses):
        return self.get_queryset().select_subclasses(*subclasses)

    def get_subclass(self, *args, **kwargs):
        return self.get_queryset().get_subclass(*args, **kwargs)

    def instance_of(self, *models):
        return self.get_queryset().instance_of(*models)


class InheritanceManager(InheritanceManagerMixin, models.Manager):
    pass
