from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.forms import generic_inlineformset_factory
from django.core.exceptions import ValidationError
from django.db import models
from django.template.loader import render_to_string
from django.utils.html import mark_safe
from dynamic_preferences.forms import GlobalPreferenceForm
from guardian.shortcuts import get_objects_for_user

from ..utils import get_modelfields
from .fields import GenericForeignKeyField
from .layout import InlineLayout


def inlinemodelform_factory(
    request, model, object, modelfields, baseformclass, layout=None, isinline=False
):
    """Returns a form class which can handle inline-modelform sets.
    Also enable crispy forms.
    """

    class InlineFormBase(baseformclass):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
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

        def is_valid(form):
            formsets = all(
                [
                    f.formset.is_valid()
                    for f in form.fields.values()
                    if isinstance(f, InlineField)
                ]
            )
            return form.is_bound and not form.errors and formsets

        def save_inline(form, parent_object):
            """Save all instances of inline forms and set the parent object"""
            for formsetfield in [
                f for f in form.fields.values() if isinstance(f, InlineField)
            ]:
                formsetfield.formset.instance = parent_object
                for childinstance, form in zip(
                    formsetfield.formset.save(commit=False), formsetfield.formset
                ):
                    for name, field in form.fields.items():
                        if isinstance(field, GenericForeignKeyField):
                            setattr(childinstance, name, form.cleaned_data[name])
                    childinstance.save()

    attribs = {}
    for modelfield in modelfields:
        if isinstance(modelfield, GenericForeignKey):
            choices = []
            initial = getattr(object, modelfield.name) if object is not None else None
            required = not model._meta.get_field(modelfield.ct_field).blank
            if hasattr(modelfield, "lazy_choices"):
                choices = modelfield.lazy_choices(modelfield, request, object)
            attribs[modelfield.name] = GenericForeignKeyField(
                choices=GenericForeignKeyField.objects_to_choices(choices),
                initial=initial,
                required=required,
            )
        elif modelfield.one_to_many or (
            modelfield.one_to_one and not modelfield.concrete
        ):

            formset_class = _generate_formset_class(
                modelfield, request, baseformclass, model, layout,
            )

            if request.POST:
                attribs[modelfield.name] = InlineField(
                    formset_class(request.POST, request.FILES, instance=object)
                )
            else:
                attribs[modelfield.name] = InlineField(formset_class(instance=object))

    patched_formclass = type(
        f"{model.__name__}GenericForeignKeysModelForm", (InlineFormBase,), attribs
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

    layout = None
    fields = ["__all__"]
    # extract the layout object for the inline field from the parent if available
    if parent_layout:
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

    formclass = inlinemodelform_factory(
        request,
        modelfield.related_model,
        None,
        child_fields.values(),
        baseformclass,
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
        ret.widget = forms.TextInput(attrs={"class": "datepicker"})

    # activate materializecss timepicker
    if isinstance(field, models.TimeField):
        ret.widget = forms.TextInput(attrs={"class": "timepicker"})

    # activate materializecss text area. Be a bit more selective here
    # Some external widgets want to use textarea for special things (e.g. CKEditor)
    if type(ret) == forms.CharField and type(ret.widget) == forms.Textarea:
        ret.widget.attrs.update({"class": "materialize-textarea"})

    # activate materializecss validation
    if "class" not in ret.widget.attrs:
        ret.widget.attrs["class"] = ""
    ret.widget.attrs["class"] += " validate"

    # apply permissions for querysets
    if hasattr(ret, "queryset"):
        qs = ret.queryset
        ret.queryset = get_objects_for_user(
            request.user, f"view_{qs.model.__name__.lower()}", qs, with_superuser=True,
        )
    return ret


class BoundInlineField(forms.BoundField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label = ""

    def as_widget(self, widget=None, attrs=None, only_initial=False):
        return render_to_string(
            "materialize_forms/inline_formset.html",
            {
                "formset": self.field.formset,
                "form_show_errors": True,
                "form_show_labels": True,
            },
        )


class InlineField(forms.Field):
    def __init__(self, formset, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.formset = formset

    def get_bound_field(self, form, field_name):
        return BoundInlineField(form, self, field_name)

    def clean(self, value):
        if not self.formset.is_valid():
            raise ValidationError(
                f"Error in list {self.formset.queryset.model._meta.verbose_name_plural.title()}"
            )
        return self.formset.queryset


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
