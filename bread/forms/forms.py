from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.forms import generic_inlineformset_factory
from django.db import models, transaction
from django.utils.html import mark_safe
from dynamic_preferences.forms import GlobalPreferenceForm
from guardian.shortcuts import get_objects_for_user

from ..utils import get_modelfields
from .fields import FormsetField, GenericForeignKeyField
from .layout import InlineLayout


def breadmodelform_factory(
    request, model, modelfields, instance, baseformclass, layout=None, isinline=False
):
    """Returns a form class which can handle inline-modelform sets and generic foreign keys.
    Also enable crispy forms.
    """

    class BreadModelFormBase(baseformclass):
        field_order = baseformclass.field_order or list(modelfields)

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
                self.helper.add_input(Submit("submit", "Save & return"))
                self.helper.add_input(
                    Submit(
                        "quicksave",
                        mark_safe(
                            f'<i class="material-icons" style="vertical-align:middle">save</i>'
                        ),
                        css_class="btn-floating btn-large",
                        style="float: right; position: sticky; bottom: 1rem; margin-right: -6rem",
                        template="materialize_forms/layout/button.html",
                    )
                )
            self.helper.layout = layout

        def save(self, *args, **kwargs):
            with transaction.atomic():
                kwargs["commit"] = False
                forminstance = super().save(*args, **kwargs)
                # GenericForeignKey might need a resafe because we set the v
                for fieldname, field in self.fields.items():
                    if isinstance(field, GenericForeignKeyField):
                        setattr(forminstance, fieldname, self.cleaned_data[fieldname])
                forminstance.save()

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
            queue.extend(getattr(elem, "fields", []))

    child_fields = get_modelfields(modelfield.related_model, fields, for_form=True)
    child_fields = {
        fieldname: field
        for fieldname, field in child_fields.items()
        if (field != modelfield.remote_field and field.editable is not False)
        or isinstance(field, GenericForeignKey)
    }

    formclass = breadmodelform_factory(
        request=request,
        model=modelfield.related_model,
        modelfields=child_fields.values(),
        instance=None,
        baseformclass=baseformclass,
        layout=layout,
        isinline=True,
    )

    if isinstance(modelfield, GenericRelation):
        formset = generic_inlineformset_factory(
            modelfield.related_model,
            ct_field=modelfield.content_type_field_name,
            fk_field=modelfield.object_id_field_name,
            fields=list(child_fields.keys()),
            formfield_callback=lambda field: _formfield_callback_with_request(
                field, request, modelfield.related_model
            ),
            form=formclass,
            extra=1,
            can_delete=True,
        )
    else:
        formset = forms.models.inlineformset_factory(
            model,
            modelfield.related_model,
            fields=list(child_fields.keys()),
            formfield_callback=lambda field: _formfield_callback_with_request(
                field, request, model
            ),
            form=formclass,
            extra=1,
            can_delete=True,
        )

    return formset


def _formfield_callback_with_request(field, request, model):
    """
    Internal function to adjust formfields and widgets to the following:
    - Replace select widgets with autocomplete widgets
    - Replace DateTimeField with SplitDateTimeField
    - Add materializecss classes for datepicker, timepicker, textarea and validation
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

    # always use splitdatetimefield because we have no good datetime picker
    if isinstance(field, models.DateTimeField):
        ret = forms.SplitDateTimeField()
        for f, _class in zip(ret.fields, ["datepicker", "timepicker"]):
            if "class" not in f.widget.attrs:
                f.widget.attrs["class"] = ""
            f.widget.attrs["type"] = "text"
            f.widget.attrs["class"] += " " + _class

    # activate materializecss datepicker
    if isinstance(field, models.DateField):
        ret.widget.attrs["class"] = ret.widget.attrs.get("class", "") + " datepicker"

    # activate materializecss timepicker
    if isinstance(field, models.TimeField):
        ret.widget.attrs["class"] = ret.widget.attrs.get("class", "") + " timepicker"

    # activate materializecss text area. Be a bit more selective here
    # Some external widgets want to use textarea for special things (e.g. CKEditor)
    if type(ret) == forms.CharField and type(ret.widget) == forms.Textarea:
        ret.widget.attrs.update({"class": "materialize-textarea"})

    # activate materializecss validation
    ret.widget.attrs["class"] = ret.widget.attrs.get("class", "") + " validate"

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
