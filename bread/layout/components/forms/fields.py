import warnings

import htmlgenerator as hg

from .helpers import ErrorList, HelpText, Label
from .widgets import BaseWidget, HiddenInput, TextInput


class FormFieldMarker(hg.BaseElement):
    # Internal helper class to mark form fields inside a render tree
    # so that the fields an be automatically extracted from it in to
    # generate a django form class
    def __init__(self, fieldname, field):
        self.fieldname = fieldname
        super().__init__(field)


def FormField(
    fieldname=None,
    form="_bread_form",
    label=None,
    help_text=None,
    error_list=None,
    inputelement_attrs=None,
    formfield_class=None,
    with_wrapper=True,
    show_hidden_initial=False,
    **kwargs,
):
    """
    Function to produce a carbon design based form field widget which is
    compatible with Django forms and based on htmlgenerator.
    """

    #
    hidden = None
    if show_hidden_initial:
        hidden = FormField(
            fieldname=fieldname,
            form=form,
            inputelement_attrs=inputelement_attrs,
            formfield_class=HiddenInput,
            with_wrapper=False,
            show_hidden_initial=False,
            **kwargs,
        )

    inputelement_attrs = inputelement_attrs or {}
    boundfield = None

    # warnings for deprecated API usage
    if "widgetattributes" in kwargs:
        warnings.warn(
            "FormField does no longer support the parameter 'widgetattributes'. "
            "The parameter 'inputelement_attrs' serves the same purpose'"
        )
    if "elementattributes" in kwargs:
        warnings.warn(
            "FormField does no longer support the parameter 'elementattributes'. "
            "attributes can now be directly passed as kwargs."
        )

    # check if this field will be used with a django form
    # if yes, derive the according values lazyly from the context
    if fieldname is not None and form is not None:
        if isinstance(form, str):
            form = hg.C(form)

        label = label or form[fieldname].label
        help_text = help_text or form.fields[fieldname].help_text
        error_list = error_list or form[fieldname].errors

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
    label_element = Label(
        label,
        required=inputelement_attrs.get("required"),
        disabled=inputelement_attrs.get("disabled"),
        _for=labelfor,
    )
    help_text_element = HelpText(help_text, disabled=inputelement_attrs.get("disabled"))
    error_element = ErrorList(error_list)

    # instantiate field (might create a lazy element when using guess_fieldclass)
    formfield_class = formfield_class or guess_fieldclass(fieldname, form)
    ret = formfield_class(
        boundfield=boundfield,
        label_element=label_element,
        help_text_element=help_text_element,
        error_element=error_element,
        inputelement_attrs=inputelement_attrs,
        **kwargs,
    )
    if show_hidden_initial:
        ret = hg.BaseElement(ret, hidden)
    if with_wrapper:
        ret = ret.with_fieldwrapper()
    return FormFieldMarker(fieldname, ret)


def guess_fieldclass(fieldname, form):
    widget_map = {}
    for cls in _all_subclasses(BaseWidget):
        if cls.django_widget not in widget_map:
            widget_map[cls.django_widget] = []
        widget_map[cls.django_widget].append(cls)

    def wrapper(context):
        realform = hg.resolve_lazy(form, context)
        widgetclass = type(realform[fieldname].field.widget)
        fieldclass = type(realform[fieldname].field)
        if widgetclass not in widget_map:
            warnings.warn(
                f"Form field {type(realform).__name__}.{fieldname} ({fieldclass}) uses widget {widgetclass} but "
                "bread has no implementation, default to TextInput"
            )

        if fieldclass in widget_map:
            return widget_map[fieldclass][0]
        if widgetclass in widget_map:
            return widget_map[widgetclass][0]
        return TextInput

    return hg.F(wrapper)


def _all_subclasses(cls):
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in _all_subclasses(c)]
    )
