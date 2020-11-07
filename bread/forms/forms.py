from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.forms import generic_inlineformset_factory
from django.db import transaction
from dynamic_preferences.forms import GlobalPreferenceForm
from dynamic_preferences.users.forms import UserPreferenceForm
from guardian.shortcuts import get_objects_for_user

from ..layout import InlineLayout
from ..layout.components.plisplate.form import Form
from ..utils import get_modelfields
from .fields import FormsetField, GenericForeignKeyField


def breadmodelform_factory(
    request,
    model,
    fields,
    instance,
    baseformclass,
    layout,
    submit_buttons,
    isinline=False,
):
    """Returns a form class which can handle inline-modelform sets and generic foreign keys.
    Also enable crispy forms.
    """
    modelfields = get_modelfields(model, fields, for_form=True).values()

    class BreadModelFormBase(baseformclass):
        field_order = baseformclass.field_order or list(fields)

        def __init__(self, data=None, files=None, initial=None, **kwargs):
            inst = kwargs.get("instance", instance)
            formsetinitial = {}
            for name, field in self.declared_fields.items():
                if isinstance(field, FormsetField):
                    formsetinitial[name] = {"instance": inst}
                if isinstance(field, GenericForeignKeyField):
                    modelfield = [f for f in modelfields if f.name == name][0]
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
                data=data, files=files, initial=formsetinitial, **kwargs,
            )

            self.helper = FormHelper(self)
            if isinline:
                self.helper.form_tag = False
            else:
                self.helper.inputs.extend(submit_buttons)
            self.helper.layout = layout

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

    # GenericForeignKey and one-to-n fields need to be defined separatly
    attribs = {}
    for modelfield in modelfields:
        if isinstance(modelfield, GenericForeignKey):
            attribs[modelfield.name] = GenericForeignKeyField(
                required=not model._meta.get_field(modelfield.fk_field).blank
            )
        elif modelfield.one_to_many or (
            modelfield.one_to_one and not modelfield.concrete
        ):
            attribs[modelfield.name] = FormsetField(
                _generate_formset_class(
                    modelfield, request, baseformclass, model, layout
                ),
                instance,
            )
    patched_formclass = type(
        f"{model.__name__}BreadModelForm", (BreadModelFormBase,), attribs
    )
    ret = forms.modelform_factory(
        model,
        form=patched_formclass,
        fields=[f.name for f in modelfields if not f.one_to_many and f.editable],
        formfield_callback=lambda field: _formfield_callback_with_request(
            field, request, model
        ),
    )
    return ret


def _generate_formset_class(modelfield, request, baseformclass, model, parent_layout):
    """Returns a FormSet class which handles inline forms correctly."""

    # determine the inline form fields, called child_fields
    layout = None
    additional_formset_kwargs = {}
    fields = ["__all__"]
    if parent_layout:
        # extract the layout object for the inline field from the parent if available
        queue = [parent_layout]
        while queue and not layout:
            elem = queue.pop()
            if isinstance(elem, InlineLayout) and elem.fieldname == modelfield.name:
                layout = elem.get_inline_layout()
                fields = [
                    i[1]
                    for i in layout.get_field_names()
                    if i[1] != forms.formsets.DELETION_FIELD_NAME
                ]
                additional_formset_kwargs = elem.formset_kwargs
            queue.extend(getattr(elem, "fields", []))

    child_fields = [
        field.name
        for field in get_modelfields(
            modelfield.related_model, fields, for_form=True
        ).values()
        if (field != modelfield.remote_field and field.editable is not False)
        or isinstance(field, GenericForeignKey)
    ]

    formclass = breadmodelform_factory(
        request=request,
        model=modelfield.related_model,
        fields=child_fields,
        instance=None,
        baseformclass=baseformclass,
        layout=layout,
        submit_buttons=[],
        isinline=True,
    )

    formset_kwargs = {
        "fields": child_fields,
        "form": formclass,
        "extra": 1,
        "can_delete": True,
    }
    formset_kwargs.update(additional_formset_kwargs)
    if isinstance(modelfield, GenericRelation):
        formset = generic_inlineformset_factory(
            modelfield.related_model,
            ct_field=modelfield.content_type_field_name,
            fk_field=modelfield.object_id_field_name,
            formfield_callback=lambda field: _formfield_callback_with_request(
                field, request, modelfield.related_model
            ),
            **formset_kwargs,
        )
    else:
        formset = forms.models.inlineformset_factory(
            model,
            modelfield.related_model,
            formfield_callback=lambda field: _formfield_callback_with_request(
                field, request, model
            ),
            **formset_kwargs,
        )

    return formset


def _formfield_callback_with_request(field, request, model):
    """
    Internal function to adjust formfields and widgets to the following:
    - Replace select widgets with autocomplete widgets
    - Replace DateTimeField with SplitDateTimeField
    - Apply result of lazy-choice and lazy-init function if set for the modelfield
    - Filter based base on object-level permissions if a queryset is used for the field
    """

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
            request.user, f"view_{qs.model.__name__.lower()}", qs, with_superuser=True,
        )
    return ret


class FilterForm(forms.Form):
    """Helper class to enable crispy-forms on the filter-forms."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_method = "get"
        self.helper.add_input(Submit("submit", "Filter"))
        self.helper.add_input(Submit("reset", "Reset"))


class PreferencesForm(GlobalPreferenceForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.add_input(Submit("submit", "Save"))


class UserPreferencesForm(UserPreferenceForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.add_input(Submit("submit", "Save"))


class BreadAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.add_input(Submit("submit", "Login"))
        self.plisplate = Form.from_django_form(self)
