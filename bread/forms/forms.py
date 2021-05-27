import htmlgenerator as hg
from django import forms
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.forms import generic_inlineformset_factory
from django.core.exceptions import FieldDoesNotExist
from django.db import models, transaction
from django.forms.formsets import DELETION_FIELD_NAME, ORDERING_FIELD_NAME
from dynamic_preferences.forms import GlobalPreferenceForm
from dynamic_preferences.users.forms import UserPreferenceForm
from guardian.shortcuts import get_objects_for_user

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


def breadmodelform_factory(  # noqa
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
                        if self.cleaned_data[fieldname].can_order:
                            order = [
                                f.instance.pk
                                for f in self.cleaned_data[fieldname].ordered_forms
                            ]
                            getattr(
                                forminstance,
                                f"set_{self.cleaned_data[fieldname].model._meta.model_name}_order",
                            )(order)

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
                    request,
                    model,
                    modelfield,
                    baseformclass,
                    formfieldelement,
                    instance,
                ),
                instance,
                formfieldelement.formsetinitial,
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
            field, request, model, instance
        ),
    )
    return ret


class InlineFormSetWithLimits(forms.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        self._queryset = super().get_queryset()[: self.max_num]
        return self._queryset


def _generate_formset_class(
    request, model, modelfield, baseformclass, formsetfieldelement, instance
):
    """Returns a FormSet class which handles inline forms correctly."""

    formfieldelements = _get_form_fields_from_layout(
        hg.BaseElement(*formsetfieldelement)
    )  # make sure the _layout.form.FormsetField does not be considered recursively

    formclass = breadmodelform_factory(
        request=request,
        model=modelfield.related_model,
        layout=formfieldelements,
        instance=instance,
        baseformclass=baseformclass,
    )

    base_formset_kwargs = {
        "fields": [
            formfieldelement.fieldname for formfieldelement in formfieldelements
        ],
        "form": formclass,
        "extra": 1 - bool(getattr(instance, modelfield.name).count()),
        "can_delete": True,
    }
    base_formset_kwargs.update(formsetfieldelement.formsetfactory_kwargs)
    if isinstance(modelfield, GenericRelation):
        return generic_inlineformset_factory(
            modelfield.related_model,
            ct_field=modelfield.content_type_field_name,
            fk_field=modelfield.object_id_field_name,
            formset=InlineFormSetWithLimits,
            formfield_callback=lambda field: _formfield_callback_with_request(
                field, request, modelfield.related_model, instance
            ),
            **base_formset_kwargs,
        )
    else:
        return forms.models.inlineformset_factory(
            model,
            modelfield.related_model,
            formset=InlineFormSetWithLimits,
            formfield_callback=lambda field: _formfield_callback_with_request(
                field, request, model, instance
            ),
            fk_name=modelfield.field.name,
            **base_formset_kwargs,
        )


def _formfield_callback_with_request(field, request, model, instance):
    kwargs = {}
    choices = None
    if hasattr(field, "lazy_choices"):
        choices = field.lazy_choices(field, request, instance)
    if not (choices is None or isinstance(choices, models.QuerySet)):
        field.choices = choices

    if hasattr(field, "lazy_initial"):
        kwargs["initial"] = field.lazy_initial(field, request, instance)

    ret = field.formfield(**kwargs)
    if isinstance(choices, models.QuerySet):
        ret.queryset = choices

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


class FilterForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout = lambda request: _layout.form.Form.from_django_form(
            self, method="GET"
        )


class PreferencesForm(GlobalPreferenceForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout = lambda request: _layout.form.Form.from_fieldnames(
            hg.C("form"), self.fields
        )


class UserPreferencesForm(UserPreferenceForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout = lambda request: _layout.form.Form.from_fieldnames(
            hg.C("form"), self.fields
        )


def _get_form_fields_from_layout(layout):
    INTERNAL_FIELDS = [DELETION_FIELD_NAME, ORDERING_FIELD_NAME]

    def walk(element):
        # do not descend into formsets, they need to be gathered separately
        if isinstance(element, _layout.form.FormsetField):
            yield element
            return
        # do not descend into script tags because we keep formset-empty form templates there
        if isinstance(element, hg.SCRIPT):
            return
        if (
            isinstance(element, _layout.form.FormField)
            and element.fieldname not in INTERNAL_FIELDS
        ):
            yield element
        for e in element:
            if isinstance(e, hg.BaseElement):
                yield from walk(e)

    return list(walk(layout))
