from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import FieldDoesNotExist
from django.db import models


def pretty_fieldname(field):
    """Will print a human readable name for a field"""
    if field.is_relation and field.one_to_many:
        return field.target_field.model._meta.verbose_name_plural.title()
    elif field.is_relation and field.many_to_many and field.auto_created:
        return (
            getattr(
                field.target_field,
                "related_name",
                field.related_model._meta.verbose_name_plural.title(),
            )
            .replace("_", " ")
            .title()
        )
    elif field.is_relation and field.one_to_one:
        return field.target_field.model._meta.verbose_name.title()
    elif isinstance(field, GenericForeignKey):
        return field.name.replace("_", " ").title()
    else:
        return field.verbose_name.title()


def title(label):
    if label and label[0].islower():
        return label.title()
    return label


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
        f"{instance._meta.app_label}.{operation}_{instance._meta.model_name}", instance
    ) or user.has_perm(
        f"{instance._meta.app_label}.{operation}_{instance._meta.model_name}"
    )


def parse_fieldlist_simple(model, fields_parameter):
    if "__all__" in fields_parameter:
        concrete_fields = [
            f.name for f in model._meta.get_fields() if f.concrete and f.name != "id"
        ]
        i = fields_parameter.index("__all__")
        fields_parameter = (
            fields_parameter[:i] + concrete_fields + fields_parameter[i + 1 :]
        )
    return fields_parameter


def _parse_fieldlist(model, fields_parameter):

    # filter fields which cannot be processed in a form
    def form_filter(field):
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
            or field.one_to_one,
        )

    # filter generic foreign key and id field out
    genericfk_exclude = set()
    for f in model._meta.get_fields():
        if isinstance(f, GenericForeignKey):
            genericfk_exclude.add(f.ct_field)
            genericfk_exclude.add(f.fk_field)

    def unwanted_fields_filter(field):
        modelfield = {
            f.get_accessor_name() if hasattr(f, "get_accessor_name") else f.name: f
            for f in model._meta.get_fields()
        }.get(field)
        # do not include the one-to-one field to a parent-model table
        if (
            hasattr(modelfield, "remote_field")
            and modelfield.remote_field
            and getattr(modelfield.remote_field, "parent_link", False) is True
        ):
            return False
        return field not in genericfk_exclude and field != "id"

    # default configuration: display only direct defined fields on the modle (no reverse related models)
    if "__all__" in fields_parameter:
        concrete_fields = [f.name for f in model._meta.get_fields() if f.concrete]
        i = fields_parameter.index("__all__")
        fields_parameter = (
            fields_parameter[:i] + concrete_fields + fields_parameter[i + 1 :]
        )
    ret = filter(unwanted_fields_filter, fields_parameter)
    ret = filter(form_filter, ret)
    return list(ret)


def get_modelfields(model, fieldlist):
    fieldlist = _parse_fieldlist(model, fieldlist)

    fields = {}
    modelfields = {f.name: f for f in model._meta.get_fields()}
    modelfields_rel = {
        f.get_accessor_name(): f
        for f in modelfields.values()
        if hasattr(f, "get_accessor_name")
    }
    for field in fieldlist:
        if field in modelfields:
            fields[field] = modelfields[field]
        elif field in modelfields_rel:
            fields[field] = modelfields_rel[field]
        else:
            raise FieldDoesNotExist(field)
        if isinstance(fields[field], GenericForeignKey):
            fields[field].sortable = False
    return fields


def resolve_relationship(model, accessor_str):
    """Converts django lookup expressions which span relationships into a list of (model, field) tuples.
    The sting "author__name" will yield [(Book, ForeignKey(Author)), (Author, CharField())]
    """
    ret = []
    fields = accessor_str.split(models.constants.LOOKUP_SEP)
    for field in fields:
        try:
            modelfield = model._meta.get_field(field)
        except FieldDoesNotExist:
            break
        ret.append((model, modelfield))
        model = getattr(modelfield.remote_field, "model", model)
    return ret
