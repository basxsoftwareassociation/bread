from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.forms import generic_inlineformset_factory
from django.db import models
from django.forms import (
    BoundField,
    ClearableFileInput,
    Field,
    FileInput,
    Select,
    SelectMultiple,
    modelform_factory,
)
from django.template.loader import render_to_string
from guardian.shortcuts import get_objects_for_user

from ..utils import get_modelfields, parse_fieldlist
from .fields import GenericForeignKeyField
from .widgets import AutocompleteSelect, AutocompleteSelectMultiple


class BoundInlineField(BoundField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label = ""

    def as_widget(self, widget=None, attrs=None, only_initial=False):
        return render_to_string(
            "materialize/table_inline_formset.html",
            {
                "formset": self.field.formset,
                "form_show_errors": True,
                "form_show_labels": True,
            },
        )


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
    request, model, object, modelfields, baseformclass, layout=None
):
    """Returns a form class which can handle inline-modelform sets.
    Also enable crispy forms.
    """

    def crispy_form_init(self, *args, **kwargs):
        super(baseformclass, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.add_input(Submit("submit", "Save"))
        self.helper.layout = layout

    attribs = {
        "__init__": crispy_form_init,
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
        elif modelfield.one_to_many or (
            modelfield.one_to_one and not modelfield.concrete
        ):
            child_fields = get_modelfields(
                modelfield.related_model,
                parse_fieldlist(modelfield.related_model, ["__all__"], is_form=True),
            )
            child_fields = {
                fieldname: field
                for fieldname, field in child_fields.items()
                if field != modelfield.remote_field and field.editable is not False
            }
            formclass = inlinemodelform_factory(
                request,
                modelfield.related_model,
                None,
                child_fields.values(),
                baseformclass,
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
                )
            else:
                formset = forms.models.inlineformset_factory(
                    model,
                    modelfield.related_model,
                    fields=list(child_fields.keys()),
                    formfield_callback=lambda field: formfield_callback_with_request(
                        field, request
                    ),
                    form=formclass,
                    extra=1,
                    can_delete=True,
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

    ret = field.formfield()

    # check if autocomplete is necessary
    if isinstance(ret.widget, SelectMultiple):
        ret = field.formfield(widget=AutocompleteSelectMultiple)
    elif isinstance(ret.widget, Select):
        ret = field.formfield(widget=AutocompleteSelect)
    elif isinstance(ret.widget, ClearableFileInput):
        ret = field.formfield(widget=FileInput)

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

    # lazy choices
    if hasattr(field, "lazy_choices"):
        field.choices = field.lazy_choices(request, object)

    # lazy initial
    if ret and hasattr(field, "lazy_initial"):
        ret.initial = field.lazy_initial(request, object)

    # apply permissions for querysets
    if hasattr(ret, "queryset"):
        qs = ret.queryset
        ret.queryset = get_objects_for_user(
            request.user, f"view_{qs.model.__name__.lower()}", qs, with_superuser=True,
        )
    return ret
