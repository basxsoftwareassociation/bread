import warnings
from typing import List, Optional, Type, Union

import htmlgenerator as hg
from django import forms

from .helpers import ErrorList, HelpText, Label
from .widgets import BaseWidget, HiddenInput, TextInput

DEFAULT_FORM_CONTEXTNAME = "__bread_form"
DEFAULT_FORMSET_CONTEXTNAME = "__bread_formset_form"


class FormFieldMarker(hg.BaseElement):
    # Internal helper class to mark form fields inside a render tree
    # so that the fields an be automatically extracted from it in to
    # generate a django form class, see bread.forms.forms
    def __init__(self, fieldname, field):
        self.fieldname = fieldname
        super().__init__(field)


def generate_widget_element(
    fieldname: str = None,  # required to derive the widget from a django form field
    form: Union[
        forms.Form, hg.Lazy, str
    ] = DEFAULT_FORM_CONTEXTNAME,  # required to derive the widget from a django form field
    no_wrapper: bool = False,  # wrapper produces less dense layout, from carbon styles
    no_label: bool = False,
    no_helptext: bool = False,
    show_hidden_initial: bool = False,  # required in special cases to add an initial value
    #
    #
    # --------------------------------------------------------------------------
    # parameters which are normally not required, when using a django form field
    # but can be filled in to create form fields independently from django form fields or
    # manually overriding values from the form field
    widgetclass: Optional[
        Union[Type[BaseWidget], hg.Lazy]
    ] = None,  # normally be taken from the django form field, will be carbon-ized
    label: Union[
        str, hg.BaseElement
    ] = None,  # normally be taken from the django form field, will be carbon-ized
    help_text: Union[
        str, hg.BaseElement
    ] = None,  # normally be taken from the django form field, will be carbon-ized
    errors: Optional[
        List[str]
    ] = None,  # normally be taken from the django form field, will be carbon-ized
    inputelement_attrs: Optional[
        Union[dict, hg.Lazy]
    ] = None,  # normally be taken from the django form field, will be carbon-ized
    **attributes,
) -> FormFieldMarker:
    """
    Function to produce a carbon design based form field widget which is
    compatible with Django forms and based on htmlgenerator.
    """

    hidden = None
    if show_hidden_initial:
        hidden = generate_widget_element(
            fieldname=fieldname,
            form=form,
            inputelement_attrs=inputelement_attrs,
            widgetclass=HiddenInput,
            no_wrapper=True,
            no_label=True,
            no_helptext=True,
            show_hidden_initial=False,
            **attributes,
        )

    inputelement_attrs = inputelement_attrs or {}
    boundfield = None

    # warnings for deprecated API usage
    if "widgetattributes" in attributes:
        warnings.warn(
            "FormField does no longer support the parameter 'widgetattributes'. "
            "The parameter 'inputelement_attrs' serves the same purpose'"
        )
    if "elementattributes" in attributes:
        warnings.warn(
            "FormField does no longer support the parameter 'elementattributes'. "
            "attributes can now be directly passed as kwargs."
        )

    # check if this field will be used with a django form if yes, derive the
    # according values lazyly from the context
    if fieldname is not None and form is not None:
        if isinstance(form, str):
            form = hg.C(form)

        label = label or form[fieldname].label
        help_text = help_text or form.fields[fieldname].help_text
        errors = errors or form[fieldname].errors

        # do this to preserve the original inputelement_attrs in the
        # buildattribs scope
        orig_inputattribs = inputelement_attrs

        def buildattribs(context):
            realform = hg.resolve_lazy(form, context)
            id = None
            if realform[fieldname].auto_id and "id" not in orig_inputattribs:
                id = (
                    realform[fieldname].html_initial_id
                    if show_hidden_initial
                    else realform[fieldname].auto_id
                )
            return {
                "id": id,
                "name": realform[fieldname].html_initial_name
                if show_hidden_initial
                else realform[fieldname].html_name,
                "value": realform[fieldname].value(),
                **realform[fieldname].build_widget_attrs({}),
                **realform[fieldname].field.widget.attrs,
                **orig_inputattribs,
            }

        inputelement_attrs = hg.F(buildattribs)
        labelfor = form[fieldname].id_for_label
        boundfield = form[fieldname]
    else:
        labelfor = inputelement_attrs.get("id")

    # helper elements
    label = Label(
        label,
        required=inputelement_attrs.get("required"),
        disabled=inputelement_attrs.get("disabled"),
        _for=labelfor,
    )
    help_text = HelpText(help_text, disabled=inputelement_attrs.get("disabled"))
    errors = ErrorList(errors)

    # instantiate field (might create a lazy element when using _guess_widget)
    widgetclass = _guess_widget(fieldname, form, widgetclass)
    ret = widgetclass(
        label=None if no_label else label,
        help_text=None if no_helptext else help_text,
        errors=errors,
        inputelement_attrs=inputelement_attrs,
        boundfield=boundfield,
        **attributes,
    )
    if show_hidden_initial:
        ret = hg.BaseElement(ret, hidden)
    if not no_wrapper:
        ret = hg.If(
            hg.F(
                lambda c: isinstance(
                    hg.resolve_lazy(boundfield, c).field.widget, forms.HiddenInput
                )
            ),
            ret,
            ret.with_fieldwrapper(),
        )
    return FormFieldMarker(fieldname, ret)


# Using this alias we can prevent a huge refactoring across multiple repos This
# is slightly inconsistent with the default naming scheme of python where camel
# case denotes not a function but a class
# TODO: maybe refactor Formfield to be formfield
FormField = generate_widget_element


def _guess_widget(fieldname, form, suggested_widgetclass) -> hg.Lazy:
    widget_map: dict = {}
    for cls in _all_subclasses(BaseWidget):
        if cls.django_widget not in widget_map:
            widget_map[cls.django_widget] = []
        widget_map[cls.django_widget].append(cls)

    def wrapper(context):
        realform = hg.resolve_lazy(form, context)
        widgetclass = type(realform[fieldname].field.widget)
        fieldclass = type(realform[fieldname].field)

        # Hidden widgets have highest priority
        if issubclass(widgetclass, forms.HiddenInput):
            return HiddenInput
        # Manually passed widgets have second priority
        if suggested_widgetclass is not None:
            return suggested_widgetclass

        # Automated detection via django-bread-widget-mapp have lowest priority
        if fieldclass in widget_map:
            return widget_map[fieldclass][0]
        if widgetclass in widget_map:
            return widget_map[widgetclass][0]

        # Fallback for unknown widgets
        warnings.warn(
            f"Form field {type(realform).__name__}.{fieldname} ({fieldclass}) uses widget {widgetclass} but "
            "bread has no implementation, default to TextInput"
        )
        return TextInput

    return hg.F(wrapper)


def _all_subclasses(cls):
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in _all_subclasses(c)]
    )
