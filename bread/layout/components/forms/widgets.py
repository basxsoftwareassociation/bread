import htmlgenerator as hg
from django.forms import widgets
from django.utils.translation import gettext_lazy as _
from phonenumber_field.formfields import PhoneNumberField

from ..button import Button
from ..icon import Icon

# Missing widget implementations:
# DateInput
# DateTimeInput
# TimeInput
# Textarea
# CheckboxInput
# NullBooleanSelect
# SelectMultiple
# RadioSelect
# CheckboxSelectMultiple
# FileInput
# ClearableFileInput
# MultipleHiddenInput
# SplitDateTimeWidget
# SplitHiddenDateTimeWidget
# SelectDateWidget


# A plain, largely unstyled input element
# It provides the basic structure for fields used
# in bread forms
class BaseWidget(hg.DIV):
    # used to mark that this class can be used in place of the according django widget or field
    django_widget = None
    django_field = None

    # default attributes which are used to create the input element in a standard way
    carbon_input_class = ""
    carbon_input_error_class = ""
    input_type = None

    # __init__ should support the following parameters
    # boundfield,
    # label_element,
    # help_text_element,
    # error_element,
    # inputelement_attrs,

    def get_input_element(self, inputelement_attrs, error_element):
        return hg.INPUT(
            type=self.input_type,
            lazy_attributes=_append_classes(
                inputelement_attrs or {},
                self.carbon_input_class,
                hg.If(
                    getattr(error_element, "condition", False),
                    self.carbon_input_error_class,
                ),
            ),
        )

    def with_fieldwrapper(self):
        return hg.DIV(self, _class="bx--form-item")


class HiddenInput(BaseWidget):
    django_widget = widgets.HiddenInput
    input_type = "hidden"

    def __init__(
        self,
        boundfield,
        label_element,
        help_text_element,
        error_element,
        inputelement_attrs,
        **attributes,
    ):
        super().__init__(self.get_input_element(inputelement_attrs, error_element))


class TextInput(BaseWidget):
    django_widget = widgets.TextInput
    carbon_input_class = "bx--text-input"
    carbon_input_error_class = "bx--text-input--invalid"
    input_type = "text"

    def __init__(
        self,
        boundfield,
        label_element,
        help_text_element,
        error_element,
        inputelement_attrs,
        icon=None,
        **attributes,
    ):
        attributes["_class"] = attributes.get("_class", "") + " bx--text-input-wrapper"

        super().__init__(
            label_element,
            hg.DIV(
                hg.If(
                    error_element.condition,
                    Icon(
                        "warning--filled",
                        size=16,
                        _class="bx--text-input__invalid-icon",
                    ),
                ),
                self.get_input_element(inputelement_attrs, error_element),
                hg.If(
                    icon,
                    hg.If(
                        hg.F(lambda c: isinstance(icon, str)),
                        Icon(
                            icon,
                            size=16,
                            _class="text-input-icon",
                        ),
                        icon,
                    ),
                ),
                _class=(
                    "bx--text-input__field-wrapper"
                    + (" text-input-with-icon" if icon is not None else "")
                ),
                data_invalid=hg.If(error_element.condition, True),
            ),
            error_element,
            help_text_element,
            **attributes,
        )


class PhoneNumberInput(TextInput):
    input_type = "tel"
    # django_widget = None # TODO: phonenumber_field has not a special widget, how can we detect it?
    django_field = PhoneNumberField

    def __init__(self, **attributes):
        super().__init__(icon="phone", **attributes)


class UrlInput(TextInput):
    django_widget = widgets.URLInput
    input_type = "url"

    def __init__(self, **attributes):
        super().__init__(icon="link", **attributes)


class EmailInput(TextInput):
    django_widget = widgets.EmailInput
    input_type = "email"

    def __init__(self, **attributes):
        super().__init__(icon="email", **attributes)


class NumberInput(TextInput):
    django_widget = widgets.NumberInput
    input_type = "number"


class Select(BaseWidget):
    django_widget = widgets.Select
    carbon_input_class = "bx--select-input"

    def __init__(
        self,
        boundfield,
        label_element,
        help_text_element,
        error_element,
        inputelement_attrs,
        inline=False,
        optgroups=None,  # for non-django-form select elements use this
        **attributes,
    ):

        select_wrapper = hg.DIV(
            hg.SELECT(
                hg.Iterator(
                    optgroups or _gen_optgroup(boundfield),
                    "optgroup",
                    hg.If(
                        hg.C("optgroup.0"),
                        hg.OPTGROUP(
                            hg.Iterator(
                                hg.C("optgroup.1"),
                                "option",
                                hg.OPTION(
                                    hg.C("option.label"),
                                    _class="bx--select-option",
                                    value=hg.C("option.value"),
                                    lazy_attributes=hg.C("option.attrs"),
                                ),
                            ),
                            _class="bx--select-optgroup",
                            label=hg.C("optgroup.0"),
                        ),
                        hg.Iterator(
                            hg.C("optgroup.1"),
                            "option",
                            hg.OPTION(
                                hg.C("option.label"),
                                _class="bx--select-option",
                                value=hg.C("option.value"),
                                lazy_attributes=hg.C("option.attrs"),
                            ),
                        ),
                    ),
                ),
                lazy_attributes=_append_classes(
                    inputelement_attrs or {},
                    self.carbon_input_class,
                    hg.If(
                        getattr(error_element, "condition", False),
                        self.carbon_input_error_class,
                    ),
                ),
            ),
            Icon(
                "chevron--down",
                size=16,
                _class="bx--select__arrow",
                aria_hidden="true",
            ),
            hg.If(
                error_element.condition,
                Icon(
                    "warning--filled",
                    size=16,
                    _class="bx--select__invalid-icon",
                ),
            ),
            _class="bx--select-input__wrapper",
            data_invalid=hg.If(error_element.condition, True),
        )
        super().__init__(
            label_element,
            hg.If(
                inline,
                hg.DIV(
                    select_wrapper,
                    error_element,
                    _class="bx--select-input--inline__wrapper",
                ),
                select_wrapper,
            ),
            help_text_element,
            hg.If(inline, None, error_element),  # not displayed if this is inline
            _class=hg.BaseElement(
                "_class",
                " bx--select",
                hg.If(inline, " bx--select--inline"),
                hg.If(error_element.condition, " bx--select--invalid"),
                hg.If(inputelement_attrs.get("disabled"), " bx--select--disabled"),
            ),
            **attributes,
        )


class PasswordInput(TextInput):
    django_widget = widgets.PasswordInput
    carbon_input_class = "bx--password-input bx--text-input"
    carbon_input_error_class = "bx--text-input--invalid"
    input_type = "password"

    def __init__(
        self,
        label_element,
        help_text_element,
        error_element,
        inputelement_attrs,
        **attributes,
    ):
        attributes["data-text-input"] = True
        attributes["_class"] = (
            attributes.get("_class", "") + " bx--password-input-wrapper"
        )
        showhidebtn = Button(
            _("Show password"),
            icon=hg.BaseElement(
                Icon("view--off", _class="bx--icon--visibility-off", hidden="true"),
                Icon("view", _class="bx--icon--visibility-on"),
            ),
            notext=True,
        )
        # override attributes from button
        showhidebtn.attributes["_class"] = (
            "bx--text-input--password__visibility__toggle bx--tooltip__trigger "
            "bx--tooltip--a11y bx--tooltip--bottom bx--tooltip--align-center"
        )
        super().__init__(
            label_element,
            help_text_element,
            error_element,
            inputelement_attrs=_combine_lazy_dict(
                inputelement_attrs, data_toggle_password_visibility=True
            ),
            icon=showhidebtn,
            **attributes,
        )


def _append_classes(lazy_attrs, *_classes):
    def wrapper_func(context):
        _classlist = []
        for _class in _classes:
            _classlist.append(_class)
            _classlist.append(" ")
        ret = hg.resolve_lazy(lazy_attrs, context) or {}
        ret["_class"] = hg.BaseElement(ret.get("_class", ""), " ", *_classlist)
        return ret

    return hg.F(wrapper_func)


def _combine_lazy_dict(lazy_attrs, **attribs):
    return hg.F(lambda c: {**(hg.resolve_lazy(lazy_attrs, c) or {}), **attribs})


def _gen_optgroup(boundfield):
    def wrapper(context):
        bfield = hg.resolve_lazy(boundfield, context)
        return bfield.field.widget.optgroups(
            bfield.name,
            bfield.field.widget.format_value(bfield.value()),
        )

    return hg.F(wrapper)


class Checkbox(BaseWidget):
    django_widget = widgets.CheckboxInput
    carbon_input_class = "bx--checkbox"
    carbon_input_error_class = "bx--text-input--invalid"
    input_type = "checkbox"

    def __init__(
        self,
        label_element,
        help_text_element,
        error_element,
        inputelement_attrs,
        **attributes,
    ):
        attributes["_class"] = (
            attributes.get("_class", "") + " bx--form-item bx--checkbox-wrapper"
        )
        self.input = hg.INPUT(**widgetattributes)
        self.label = hg.LABEL(
            self.input,
            label,
            hg.If(required, REQUIRED_LABEL),
            _class=hg.BaseElement(
                "bx--checkbox-label",
                hg.If(disabled, " bx--label--disabled"),
            ),
            data_contained_checkbox_state=hg.If(
                hg.F(lambda c: widgetattributes.get("checked", False)), "true", "false"
            ),
        )
        super().__init__(
            self.label,
            HelpText(help_text),
            ErrorList(errors),
            **attributes,
        )
