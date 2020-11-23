from dynamic_preferences.forms import GlobalPreferenceForm
from dynamic_preferences.users.forms import UserPreferenceForm
from guardian.shortcuts import get_objects_for_user

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.forms import generic_inlineformset_factory
from django.core.exceptions import FieldDoesNotExist
from django.db import transaction
from django.forms.formsets import DELETION_FIELD_NAME

from .. import layout as _layout  # prevent name clashing
from .fields import FormsetField, GenericForeignKeyField


# shortcut, actually this should always be used but class based views wanted the class separately
def generate_form(request, model, layout, instance, **kwargs):
    return breadmodelform_factory(
        request,
        model=model,
        layout=layout,
        instance=instance,
    )(
        *([request.POST, request.FILES] if request.method == "POST" else []),
        instance=instance,
        **kwargs,
    )


def breadmodelform_factory(
    request, model, layout, instance=None, baseformclass=forms.models.ModelForm
):
    """Returns a form class which can handle inline-modelform sets and generic foreign keys."""
    formfieldelements = _get_form_fields_from_layout(layout)

    class BreadModelFormBase(baseformclass):
        field_order = baseformclass.field_order or [
            f.fieldname for f in formfieldelements
        ]

        def __init__(self, data=None, files=None, initial=None, **kwargs):
            inst = kwargs.get("instance", instance)
            formsetinitial = {}
            for name, field in self.declared_fields.items():
                if isinstance(field, FormsetField):
                    formsetinitial[name] = {
                        "instance": inst,
                    }
                if isinstance(field, GenericForeignKeyField):
                    modelfield = model._meta.get_field(name)
                    if hasattr(modelfield, "lazy_choices"):
                        field.choices = GenericForeignKeyField.objects_to_choices(
                            modelfield.lazy_choices(modelfield, request, inst)
                        )
                    init = getattr(inst, modelfield.name, None)
                    if init:
                        formsetinitial[name] = GenericForeignKeyField.object_to_choice(
                            init
                        )[0]
            if initial:
                formsetinitial.update(initial)
            super().__init__(
                data=data,
                files=files,
                initial=formsetinitial,
                **kwargs,
            )

        def save(self, *args, **kwargs):
            with transaction.atomic():
                kwargs["commit"] = False
                forminstance = super().save(*args, **kwargs)
                # GenericForeignKey might need a resafe because we set the value
                for fieldname, field in self.fields.items():
                    if isinstance(field, GenericForeignKeyField):
                        setattr(forminstance, fieldname, self.cleaned_data[fieldname])
                forminstance.save()
                self.save_m2m()

                for fieldname, field in self.fields.items():
                    if isinstance(field, FormsetField):
                        self.cleaned_data[fieldname].instance = forminstance
                        self.cleaned_data[fieldname].save()
            return forminstance

    # GenericForeignKey and one-to-n fields need to be added separatly to the form class
    attribs = {}
    for formfieldelement in formfieldelements:
        try:
            modelfield = model._meta.get_field(formfieldelement.fieldname)
        except FieldDoesNotExist:
            continue
        if isinstance(modelfield, GenericForeignKey):
            attribs[modelfield.name] = GenericForeignKeyField(
                required=not model._meta.get_field(modelfield.fk_field).blank
            )
        elif modelfield.one_to_many or (
            modelfield.one_to_one and not modelfield.concrete
        ):
            attribs[modelfield.name] = FormsetField(
                _generate_formset_class(
                    request, model, modelfield, baseformclass, formfieldelement
                ),
                instance,
            )
    patched_formclass = type(
        f"{model.__name__}BreadModelForm", (BreadModelFormBase,), attribs
    )
    ret = forms.modelform_factory(
        model,
        form=patched_formclass,
        fields=[
            f.fieldname
            for f in formfieldelements
            if isinstance(f, _layout.form.FormField)
        ],
        formfield_callback=lambda field: _formfield_callback_with_request(
            field, request, model
        ),
    )
    return ret


def _generate_formset_class(
    request, model, modelfield, baseformclass, formsetfieldelement
):
    """Returns a FormSet class which handles inline forms correctly."""

    formfieldelements = _get_form_fields_from_layout(
        _layout.BaseElement(*formsetfieldelement)
    )  # make sure the _layout.form.FormSetField does not be considered recursively

    formclass = breadmodelform_factory(
        request=request,
        model=modelfield.related_model,
        layout=formfieldelements,
        instance=None,
        baseformclass=baseformclass,
    )

    base_formset_kwargs = {
        "fields": [
            formfieldelement.fieldname for formfieldelement in formfieldelements
        ],
        "form": formclass,
        "extra": 0,
        "can_delete": True,
    }
    base_formset_kwargs.update(formsetfieldelement.formset_kwargs)
    if isinstance(modelfield, GenericRelation):
        return generic_inlineformset_factory(
            modelfield.related_model,
            ct_field=modelfield.content_type_field_name,
            fk_field=modelfield.object_id_field_name,
            formfield_callback=lambda field: _formfield_callback_with_request(
                field, request, modelfield.related_model
            ),
            **base_formset_kwargs,
        )
    else:
        return forms.models.inlineformset_factory(
            model,
            modelfield.related_model,
            formfield_callback=lambda field: _formfield_callback_with_request(
                field, request, model
            ),
            **base_formset_kwargs,
        )


def _formfield_callback_with_request(field, request, model):
    modelfield = getattr(model, field.get_attname(), None)
    kwargs = {}
    if modelfield:
        if hasattr(modelfield, "lazy_choices"):
            field.choices = modelfield.lazy_choices(request, object)

        if hasattr(modelfield, "lazy_initial"):
            kwargs["initial"] = modelfield.lazy_initial(request, object)

    ret = field.formfield(**kwargs)

    # apply permissions for querysets
    if hasattr(ret, "queryset"):
        qs = ret.queryset
        ret.queryset = get_objects_for_user(
            request.user,
            f"view_{qs.model.__name__.lower()}",
            qs,
            with_superuser=True,
        )
    return ret


# TODO: the following custom forms could and probably shoudl be replace with template filters or tags
class FilterForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout = _layout.form.Form.from_django_form(self, method="GET")


class PreferencesForm(GlobalPreferenceForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout = _layout.form.Form.from_fieldnames(_layout.C("form"), self.fields)


class UserPreferencesForm(UserPreferenceForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout = _layout.form.Form.from_fieldnames(_layout.C("form"), self.fields)


class BreadAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout = _layout.form.Form.from_fieldnames(_layout.C("form"), self.fields)


def _get_form_fields_from_layout(layout):
    INTERNAL_FIELDS = [DELETION_FIELD_NAME]

    def walk(element):
        if isinstance(
            element, _layout.form.FormSetField
        ):  # do not descend into formsets
            yield element
            return
        if (
            isinstance(element, _layout.form.FormField)
            and element.fieldname not in INTERNAL_FIELDS
        ):
            yield element
        for e in element:
            if isinstance(e, _layout.BaseElement):
                yield from walk(e)

    return list(walk(layout))
