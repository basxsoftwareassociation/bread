import itertools

from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models.fields import Field


def quickregister(
    urlpatterns,
    model,
    menugroup=None,
    with_editaction=True,
    with_deleteaction=True,
    with_menuitem=True,
    **kwargs,
):
    from .. import menu
    from ..views import BrowseView
    from .links import Link, ModelHref
    from .urls import default_model_paths

    rowactions = []
    if with_editaction:
        rowactions.append(BrowseView.editlink())
    if with_deleteaction:
        rowactions.append(BrowseView.deletelink())

    kwargs["browseview"] = kwargs.get("browseview", BrowseView)._with(
        rowactions=rowactions
    )
    urlpatterns.extend(default_model_paths(model, **kwargs))

    if with_menuitem:
        menu.registeritem(
            menu.Item(
                Link(
                    ModelHref(model, "browse"),
                    model._meta.verbose_name_plural.title(),
                    permissions=[permissionname(model, "view")],
                ),
                model._meta.app_label.title() if menugroup is None else menugroup,
            )
        )


def resolve_modellookup(model, accessor):
    """Takes a model and an accessor string like 'address.street' and returns a list of the according python objects"""
    attrib = model
    attribchain = []
    for attribstr in accessor.split("."):
        if isinstance(attrib, models.Model) or (
            isinstance(attrib, type) and issubclass(attrib, models.Model)
        ):
            try:
                attrib = attrib._meta.get_field(attribstr)
            except FieldDoesNotExist:
                if attribstr in attrib.objects.none().query.annotations:
                    attrib = attribstr
                else:
                    attrib = getattr(attrib, attribstr)
        elif isinstance(attrib, models.fields.related.RelatedField):
            attrib = attrib.related_model
            try:
                attrib = attrib._meta.get_field(attribstr)
            except FieldDoesNotExist:
                if attribstr in attrib.objects.none().query.annotations:
                    attrib = attribstr
                else:
                    attrib = getattr(attrib, attribstr)
        elif isinstance(attrib, models.fields.reverse_related.ForeignObjectRel):
            try:
                attrib = attrib.related_model._meta.get_field(attribstr)
            except FieldDoesNotExist:
                attrib = getattr(attrib.related_model, attribstr)
        else:
            try:
                attrib = attrib[attribstr]
            except (TypeError, AttributeError, KeyError, ValueError, IndexError):
                attrib = getattr(attrib, attribstr)
        attribchain.append(attrib)
    return attribchain


def has_permission(user, operation, instance):
    """
    instance: can be model instance or a model
    operation is one of ["view", "add", "change", "delete"] (django defaults)
    """
    operations = ["view", "add", "change", "delete"]
    if operation not in operations:
        raise RuntimeError(
            f"argument 'operation' must be one of {operations} but was {operation}"
        )
    return user.has_perm(
        permissionname(instance, operation), instance
    ) or user.has_perm(permissionname(instance, operation))


def filter_fieldlist(model, fieldlist, for_form=False):
    if fieldlist is None:
        fieldlist = ["__all__"]
    return [
        f
        for f in expand_ALL_constant(model, fieldlist)
        if not isinstance(f, str)
        or (
            not _is_internal_field(model, f)
            and (not for_form or _can_use_in_form(model, f))
        )
    ]


def get_modelfields(model, fieldlist, for_form=False):
    from django.contrib.contenttypes.fields import GenericForeignKey

    fields = {}
    modelfields = {f.name: f for f in model._meta.get_fields()}
    modelfields_rel = {
        f.get_accessor_name(): f
        for f in modelfields.values()
        if hasattr(f, "get_accessor_name")
    }
    for field in filter_fieldlist(model, fieldlist, for_form=for_form):
        if field in modelfields:
            fields[field] = modelfields[field]
        elif field in modelfields_rel:
            fields[field] = modelfields_rel[field]
        else:
            raise FieldDoesNotExist(field)
        if isinstance(fields[field], GenericForeignKey):
            fields[field].sortable = False
    return fields


def expand_ALL_constant(model, fieldnames):
    """Replaces the constant ``__all__`` with all concrete fields of the model"""
    fieldnames = list(fieldnames)
    if "__all__" in fieldnames:
        concrete_fields = get_sorted_modelfields(model)
        i = fieldnames.index("__all__")
        return fieldnames[:i] + concrete_fields + fieldnames[i + 1 :]
    return fieldnames


def get_sorted_modelfields(model):
    # better than model._meta.get_fields because it keeps declared order of fields
    sortable_private_fields = [
        f for f in model._meta.private_fields if isinstance(f, Field)
    ]
    return [
        f.name
        for f in sorted(
            itertools.chain(
                model._meta.concrete_fields,
                sortable_private_fields,
                model._meta.many_to_many,
            )
        )
    ]


def _is_internal_field(model, field):
    """Filter generic foreign key, parent link of multi-table inheritance and id"""
    from django.contrib.contenttypes.fields import GenericForeignKey

    exclude = {model._meta.pk.name}
    for f in model._meta.get_fields():
        if isinstance(f, GenericForeignKey):
            exclude.add(f.ct_field)
            exclude.add(f.fk_field)
    modelfield = {
        f.get_accessor_name() if hasattr(f, "get_accessor_name") else f.name: f
        for f in model._meta.get_fields()
    }.get(field)
    # To check the FK to the parent table we could also put "{modelname}_ptr"
    # into the exclude list but checking for the parent_link attribute seems safer
    if (
        hasattr(modelfield, "remote_field")
        and modelfield.remote_field
        and getattr(modelfield.remote_field, "parent_link", False) is True
    ):
        return True
    return field in exclude


def _can_use_in_form(model, field):
    from django.contrib.contenttypes.fields import GenericForeignKey

    """Filter fields which cannot be processed in a form"""
    modelfields = {
        f.get_accessor_name() if hasattr(f, "get_accessor_name") else f.name: f
        for f in model._meta.get_fields(include_hidden=True)
    }
    if field not in modelfields:
        return False
    field = modelfields[field]
    return (
        field.editable
        or isinstance(field, GenericForeignKey)
        or field.many_to_many
        or field.one_to_many
        or field.one_to_one
    )


# FIX: this is super slow when used in loops
def get_concrete_instance(instance):
    """Returns the the most concrete instance of the model-instance"""
    for field in instance._meta.get_fields():
        if (
            isinstance(field, models.fields.reverse_related.OneToOneRel)
            and hasattr(field, "parent_link")
            and field.parent_link is True
        ):
            child_object = getattr(instance, field.get_accessor_name(), None)
            if child_object:
                return get_concrete_instance(child_object)
    return instance


def permissionname(model, name):
    return f"{model._meta.app_label}.{name}_{model._meta.model_name}"
