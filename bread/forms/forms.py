from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.forms import generic_inlineformset_factory

# BaseGenericInlineFormSet,
from django.db import models
from django.forms import (
    BoundField,
    Field,
    ModelChoiceField,
    ModelMultipleChoiceField,
    modelform_factory,
    widgets,
)
from django.forms.models import inlineformset_factory
from django.template.loader import render_to_string
from guardian.shortcuts import get_objects_for_user

from ..utils import get_modelfields, parse_fieldlist
from .fields import GenericForeignKeyField


class BoundInlineField(BoundField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label = ""

    def as_widget(self, widget=None, attrs=None, only_initial=False):
        return render_to_string("bread/formset.html", {"formset": self.field.formset})


class InlineField(Field):
    def __init__(self, formset, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.formset = formset

    def get_bound_field(self, form, field_name):
        return BoundInlineField(form, self, field_name)

    def clean(self, value):
        self.formset.clean()
        return self.formset.queryset


# patch modelform_factory to handl inline forms
def inlinemodelform_factory(
    request, model, object, modelfields, baseformclass, **inlineformset_factory_kwargs
):
    attribs = {
        "error_css_class": "error",
        "required_css_class": "required",
        "is_valid": is_valid_inline,
        "save_inline": save_inline,
    }

    for modelfield in modelfields:
        if isinstance(modelfield, GenericForeignKey):
            choices = []
            initial = getattr(object, modelfield.name) if object is not None else None
            required = not model._meta.get_field(modelfield.ct_field).blank
            if hasattr(modelfield, "lazy_choices"):
                choices = modelfield.lazy_choices(modelfield, request, object)
            attribs[modelfield.name] = GenericForeignKeyField(
                choices=choices, initial=initial, required=required
            )
        elif modelfield.one_to_many or modelfield.one_to_one:
            child_fields = get_modelfields(
                modelfield.related_model,
                parse_fieldlist(modelfield.related_model, ["__all__"], is_form=True),
            )
            child_fields = {
                fieldname: field
                for fieldname, field in child_fields.items()
                if field != modelfield.remote_field and field.editable is not False
            }
            if modelfield.one_to_one:
                inlineformset_factory_kwargs["max_num"] = 1
            formclass = inlinemodelform_factory(
                request,
                modelfield.related_model,
                None,
                child_fields.values(),
                baseformclass,
                **inlineformset_factory_kwargs,
            )
            if isinstance(modelfield, GenericRelation):
                formset = generic_inlineformset_factory(
                    modelfield.related_model,
                    ct_field=modelfield.content_type_field_name,
                    fk_field=modelfield.object_id_field_name,
                    fields=list(child_fields.keys()),
                    formfield_callback=lambda field: formfield_callback_with_request(
                        field, request
                    ),
                    form=formclass,
                    extra=1,
                    can_delete=True,
                    **inlineformset_factory_kwargs,
                )
            else:
                formset = inlineformset_factory(
                    model,
                    modelfield.related_model,
                    fields=list(child_fields.keys()),
                    formfield_callback=lambda field: formfield_callback_with_request(
                        field, request
                    ),
                    form=formclass,
                    extra=1,
                    can_delete=True,
                    **inlineformset_factory_kwargs,
                )
            if request.POST:
                attribs[modelfield.name] = InlineField(
                    formset(request.POST, request.FILES, instance=object)
                )
            else:
                attribs[modelfield.name] = InlineField(formset(instance=object))

    patched_formclass = type(
        f"{model.__name__}GenericForeignKeysModelForm", (baseformclass,), attribs
    )

    ret = modelform_factory(
        model,
        form=patched_formclass,
        fields=[f.name for f in modelfields if not f.one_to_many and f.editable],
        formfield_callback=lambda field: formfield_callback_with_request(
            field, request
        ),
    )
    return ret


def is_valid_inline(form):
    formsets = all(
        [
            f.formset.is_valid()
            for f in form.fields.values()
            if isinstance(f, InlineField)
        ]
    )
    return form.is_bound and not form.errors and formsets


def save_inline(form, parent_object):
    for formsetfield in [f for f in form.fields.values() if isinstance(f, InlineField)]:
        formsetfield.formset.instance = parent_object
        formsetfield.formset.save()


def formfield_callback_with_request(field, request):
    # customize certain widgets
    if isinstance(field, models.DateTimeField):
        ret = field.formfield(widget=widgets.SplitDateTimeWidget)
    else:
        ret = field.formfield()
    # lazy choices
    if hasattr(field, "lazy_choices"):
        field.choices = field.lazy_choices(request, object)
    # lazy initial
    if ret and (not ret.initial and hasattr(field, "lazy_initial")):
        ret.initial = field.lazy_initial(request, object)

    # apply permissions for foreign key choices
    if isinstance(ret, ModelChoiceField) or isinstance(ret, ModelMultipleChoiceField):
        qs = ret.queryset
        ret.queryset = get_objects_for_user(
            request.user, f"view_{qs.model.__name__.lower()}", qs, with_superuser=True,
        )
    return ret
