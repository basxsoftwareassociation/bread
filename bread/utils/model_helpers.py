from django.core.exceptions import FieldDoesNotExist
from django.db import models


def pretty_modelname(model, plural=False):
    """Canonical way to pretty print a model name"""
    if plural:
        return model._meta.verbose_name_plural
    return model._meta.verbose_name


def pretty_fieldname(field):
    from django.contrib.contenttypes.fields import GenericForeignKey

    """Canonical way to pretty print a field name"""
    if isinstance(field, str):
        ret = field.replace("_", " ")
    elif field.is_relation and field.one_to_many:
        ret = field.target_field.model._meta.verbose_name_plural
    elif field.is_relation and field.many_to_many and field.auto_created:
        ret = getattr(
            field.target_field,
            "related_name",
            field.related_model._meta.verbose_name_plural,
        ).replace("_", " ")
    elif field.is_relation and field.one_to_one:
        ret = field.target_field.model._meta.verbose_name
    elif isinstance(field, GenericForeignKey):
        ret = field.name.replace("_", " ")
    else:
        ret = field.verbose_name

    if ret and ret[0].islower():
        return ret.capitalize()
    return str(ret)


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
                attrib = getattr(attrib, attribstr)
        elif isinstance(attrib, models.fields.related.RelatedField):
            attrib = attrib.related_model
            try:
                attrib = attrib._meta.get_field(attribstr)
            except FieldDoesNotExist:
                attrib = getattr(attrib, attribstr)
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
        f"{instance._meta.app_label}.{operation}_{instance._meta.model_name}", instance
    ) or user.has_perm(
        f"{instance._meta.app_label}.{operation}_{instance._meta.model_name}"
    )


def filter_fieldlist(model, fieldlist, for_form=False):
    if fieldlist is None:
        fieldlist = ["__all__"]
    return [
        f
        for f in expand_ALL_constant(model, fieldlist)
        if not _is_internal_field(model, f)
        and (not for_form or _can_use_in_form(model, f))
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
    if "__all__" in fieldnames:
        concrete_fields = []
        for f in model._meta.get_fields():
            if f.concrete:
                if f.one_to_one or f.many_to_many:
                    concrete_fields.append(f.name)
                else:
                    concrete_fields.append(f.name)
        i = fieldnames.index("__all__")
        return fieldnames[:i] + concrete_fields + fieldnames[i + 1 :]
    return fieldnames


def _is_internal_field(model, field):
    """Filter generic foreign key, parent link of multi-table inheritance and id"""
    from django.contrib.contenttypes.fields import GenericForeignKey

    exclude = {"id"}
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
