import warnings

import htmlgenerator as hg

from ..icon import Icon
from .helpers import ErrorList, HelpText, Label


# A plain, largely unstyled input element
# It provides the basic structure for fields used
# in bread forms
class BaseFormField(hg.DIV):
    def with_fieldwrapper(self):
        return hg.DIV(self, _class="bx--form-item")


class PlainFormField(BaseFormField):
    def __init__(
        self,
        label_element=None,
        help_text_element=None,
        error_element=None,
        inputelement_attrs=None,
        **attributes,
    ):
        inputelement_attrs = inputelement_attrs or {}
        super().__init__(
            label_element,
            hg.INPUT(**inputelement_attrs),
            help_text_element,
            error_element,
            **attributes,
        )


class TextInput(BaseFormField):
    def __init__(
        self,
        label_element=None,
        help_text_element=None,
        error_element=None,
        inputelement_attrs=None,
        icon=None,
        **attributes,
    ):
        inputelement_attrs = inputelement_attrs or {}
        attributes["_class"] = attributes.get("_class", "") + " bx--text-input-wrapper"

        if isinstance(inputelement_attrs, hg.Lazy):
            input = hg.INPUT(
                type="text",
                _class=hg.BaseElement(
                    inputelement_attrs.get("_class"),
                    " bx--text-input",
                    hg.If(error_element.condition, " bx--text-input--invalid"),
                ),
                lazy_attributes=inputelement_attrs,
            )
        else:
            input = hg.INPUT(
                type="text",
                **{
                    **inputelement_attrs,
                    "_class": hg.BaseElement(
                        inputelement_attrs.get("_class", ""),
                        " bx--text-input",
                        hg.If(error_element.condition, " bx--text-input--invalid"),
                    ),
                },
            )

        fieldwrapper = hg.DIV(
            hg.If(
                error_element.condition,
                Icon(
                    "warning--filled",
                    size=16,
                    _class="bx--text-input__invalid-icon",
                ),
            ),
            input,
            hg.If(
                icon,
                Icon(
                    icon,
                    size=16,
                    _class="text-input-icon",
                ),
            ),
            _class=(
                "bx--text-input__field-wrapper"
                + (" text-input-with-icon" if icon is not None else "")
            ),
            data_invalid=hg.If(error_element.condition, True),
        )

        super().__init__(
            label_element,
            fieldwrapper,
            error_element,
            help_text_element,
            **attributes,
        )


# shortcut for most use cases, keeping backwards compatability
def FormField(
    fieldname=None,
    form=None,
    label=None,
    help_text=None,
    error_list=None,
    inputelement_attrs=None,
    formfield_class=TextInput,
    **kwargs,
):
    # todo:
    # - add support for required attribute
    # - add support for disabled attribute
    # can be removed in the future

    inputelement_attrs = inputelement_attrs or {}
    if "widgetattributes" in kwargs:
        warnings.warn(
            "FormField does no longer support the parameter 'widgetattributes'. The parameter 'inputelement_attrs' serves the same purpose'"
        )
    if "elementattributes" in kwargs:
        warnings.warn(
            "FormField does no longer support the parameter 'elementattributes'. attributes can now be directly passed as kwargs."
        )
    # check if this field will be used with a django form
    # if yes, derive the according values lazyly from the context
    if fieldname is not None and form is not None:
        if isinstance(form, str):
            form = hg.C(form)

        label = label or form[fieldname].label
        help_text = help_text or form.fields[fieldname].help_text
        error_list = error_list or form[fieldname].errors
        inputelement_attrs = form[fieldname].build_widget_attrs(inputelement_attrs)

    label_element = Label(
        label,
        required=inputelement_attrs.get("required"),
        disabled=inputelement_attrs.get("disabled"),
        _for=inputelement_attrs.get("id"),
    )
    help_text_element = HelpText(help_text, disabled=inputelement_attrs.get("disabled"))
    error_element = ErrorList(error_list)

    return formfield_class(
        label_element=label_element,
        help_text_element=help_text_element,
        error_element=error_element,
        inputelement_attrs=inputelement_attrs,
        **kwargs,
    ).with_fieldwrapper()
