import os

import htmlgenerator as hg
from _strptime import TimeRE
from django.conf import settings
from django.forms import widgets
from django.utils import formats
from django.utils.translation import gettext_lazy as _
from phonenumber_field.formfields import PhoneNumberField

from ..button import Button
from ..icon import Icon
from .helpers import REQUIRED_LABEL, ErrorList, Label, to_php_formatstr

# Missing widget implementations:
# DateTimeInput
# TimeInput
# NullBooleanSelect
# SelectMultiple
# RadioSelect
# FileInput
# ClearableFileInput
#
# less used:
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

    # default attributes which are used to create the input element in a standard way
    carbon_input_class = ""
    carbon_input_error_class = ""
    input_type = None

    # __init__ should support the following parameters
    # label_element: bread.layout.components.forms.utils.Label
    # help_text_element: Optional[Any]
    # error_element: bread.layout.components.forms.utils.ErrorList
    # inputelement_attrs: Union[Lazy[dict], dict],
    # boundfield: Optional[django.forms.BoundField],

    def __init__(self, *args, **kwargs):
        if "boundfield" in kwargs:
            del kwargs["boundfield"]
        super().__init__(*args, **kwargs)

    def get_input_element(self, inputelement_attrs, error_element, **kwargs):
        return hg.INPUT(
            type=self.input_type,
            lazy_attributes=_combine_lazy_dict(
                _append_classes(
                    inputelement_attrs or {},
                    self.carbon_input_class,
                    hg.If(
                        getattr(error_element, "condition", False),
                        self.carbon_input_error_class,
                    ),
                ),
                kwargs,
            ),
        )

    def with_fieldwrapper(self):
        return hg.DIV(self, _class="bx--form-item")


class HiddenInput(BaseWidget):
    django_widget = widgets.HiddenInput
    input_type = "hidden"

    def __init__(
        self,
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
    django_widget = PhoneNumberField

    def __init__(self, *args, **attributes):
        super().__init__(*args, icon="phone", **attributes)


class UrlInput(TextInput):
    django_widget = widgets.URLInput
    input_type = "url"

    def __init__(self, *args, **attributes):
        super().__init__(*args, icon="link", **attributes)


class EmailInput(TextInput):
    django_widget = widgets.EmailInput
    input_type = "email"

    def __init__(self, *args, **attributes):
        super().__init__(*args, icon="email", **attributes)


class NumberInput(TextInput):
    django_widget = widgets.NumberInput
    input_type = "number"


class Select(BaseWidget):
    django_widget = widgets.Select
    carbon_input_class = "bx--select-input"

    def __init__(
        self,
        label_element,
        help_text_element,
        error_element,
        inputelement_attrs,
        boundfield=None,
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
                        error_element.condition,
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
                attributes.get("_class"),
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
            label_element=label_element,
            help_text_element=help_text_element,
            error_element=error_element,
            inputelement_attrs=_combine_lazy_dict(
                inputelement_attrs, {"data_toggle_password_visibility": True}
            ),
            icon=showhidebtn,
            **attributes,
        )


class Checkbox(BaseWidget):
    django_widget = widgets.CheckboxInput
    carbon_input_class = "bx--checkbox"
    input_type = "checkbox"

    def __init__(
        self,
        label_element,
        help_text_element,
        error_element,
        inputelement_attrs,
        boundfield=None,
        **attributes,
    ):
        attributes["_class"] = hg.BaseElement(
            attributes.get("_class", ""), " bx--checkbox-wrapper"
        )
        attrs = {}
        if boundfield:
            attrs["checked"] = hg.F(
                lambda c: hg.resolve_lazy(boundfield, c).field.widget.check_test(
                    hg.resolve_lazy(boundfield, c).value()
                )
            )
        inputelement_attrs = _combine_lazy_dict(inputelement_attrs, attrs)
        super().__init__(
            hg.LABEL(
                self.get_input_element(inputelement_attrs, error_element),
                label_element.label,
                hg.If(inputelement_attrs.get("required"), REQUIRED_LABEL),
                _class=hg.BaseElement(
                    "bx--checkbox-label",
                    hg.If(inputelement_attrs.get("disabled"), " bx--label--disabled"),
                ),
                data_contained_checkbox_state=hg.If(
                    inputelement_attrs.get("checked"),
                    "true",
                    "false",
                ),
            ),
            help_text_element,
            error_element,
            **attributes,
        )


class CheckboxSelectMultiple(BaseWidget):
    django_widget = widgets.CheckboxSelectMultiple
    carbon_input_class = "bx--checkbox"
    input_type = "checkbox"

    def __init__(
        self,
        label_element,
        help_text_element,
        error_element,
        inputelement_attrs,
        boundfield=None,
        **attributes,
    ):
        super().__init__(
            label_element,
            hg.FIELDSET(
                hg.Iterator(
                    boundfield.subwidgets,
                    "checkbox",
                    Checkbox(
                        label_element=Label(hg.C("checkbox").data["label"]),
                        help_text_element=None,
                        error_element=ErrorList([]),
                        inputelement_attrs=_combine_lazy_dict(
                            _combine_lazy_dict(
                                inputelement_attrs,
                                {
                                    "name": hg.C("checkbox").data["name"],
                                    "value": hg.C("checkbox").data["value"],
                                    "checked": hg.C("checkbox").data["selected"],
                                },
                            ),
                            hg.C("checkbox").data["attrs"],
                        ),
                    ),
                )
            ),
            help_text_element,
            error_element,
            **attributes,
        )


class DatePicker(BaseWidget):
    django_widget = widgets.DateInput
    carbon_input_class = "bx--date-picker__input"
    input_type = "text"  # prevent browser style date picker but use carbon design

    def __init__(
        self,
        label_element,
        help_text_element,
        error_element,
        inputelement_attrs,
        boundfield=None,
        style_short=False,
        style_simple=False,
        **attributes,
    ):
        if not style_simple:
            attributes["data-date-picker"] = True
            attributes["data-date-picker-type"] = "single"

        attributes["_class"] = hg.BaseElement(
            attributes.get("_class"),
            " bx--date-picker",
            hg.If(style_simple, " bx--date-picker--simple", "bx--date-picker--single"),
            hg.If(style_short, " bx--date-picker--short"),
        )

        super().__init__(
            hg.DIV(
                label_element,
                hg.If(
                    style_simple,
                    self.get_input_element(
                        inputelement_attrs,
                        error_element,
                        data_invalid=hg.If(error_element.condition, True),
                        pattern=hg.F(
                            lambda c: (
                                TimeRE()
                                .compile(
                                    hg.resolve_lazy(boundfield, c).field.widget.format
                                    or formats.get_format(
                                        hg.resolve_lazy(
                                            boundfield, c
                                        ).field.widget.format_key
                                    )[0]
                                )
                                .pattern
                            )
                        ),
                    ),
                    hg.DIV(
                        self.get_input_element(
                            inputelement_attrs,
                            error_element,
                            data_date_picker_input=True,
                            data_invalid=hg.If(error_element.condition, True),
                            data_date_format=hg.F(
                                lambda c: to_php_formatstr(
                                    hg.resolve_lazy(boundfield, c).field.widget.format,
                                    hg.resolve_lazy(
                                        boundfield, c
                                    ).field.widget.format_key,
                                )
                            ),
                        ),
                        Icon(
                            "calendar",
                            size=16,
                            _class="bx--date-picker__icon",
                            data_date_picker_icon="true",
                        ),
                        _class="bx--date-picker-input__wrapper",
                    ),
                ),
                help_text_element,
                error_element,
                _class="bx--date-picker-container",
            ),
            **attributes,
        )


class Textarea(BaseWidget):
    django_widget = widgets.Textarea
    carbon_input_class = "bx--text-area bx--text-area--v2"
    carbon_input_error_class = "bx--text-area--invalid"

    def __init__(
        self,
        label_element,
        help_text_element,
        error_element,
        inputelement_attrs,
        boundfield=None,
        **attributes,
    ):
        attributes["_class"] = attributes.get("_class", "") + " bx--form-item"

        super().__init__(
            label_element,
            hg.DIV(
                hg.TEXTAREA(
                    boundfield.value(),
                    hg.If(
                        error_element.condition,
                        Icon(
                            "warning--filled",
                            size=16,
                            _class="bx--text-area__invalid-icon",
                        ),
                    ),
                    lazy_attributes=_combine_lazy_dict(
                        _append_classes(
                            inputelement_attrs or {},
                            self.carbon_input_class,
                            hg.If(
                                error_element.condition,
                                self.carbon_input_error_class,
                            ),
                        ),
                        {"value": None},
                    ),
                ),
                _class="bx--text-area__wrapper",
            ),
            help_text_element,
            error_element,
            **attributes,
        )


class FileInput(BaseWidget):
    django_widget = widgets.FileInput
    carbon_input_class = "bx--file-input bx--visually-hidden"
    input_type = "file"
    # TODO: make clearable working
    clearable = False

    def __init__(
        self,
        label_element,
        help_text_element,
        error_element,
        inputelement_attrs,
        **attributes,
    ):
        uploadbutton = hg.LABEL(
            hg.SPAN(_("Select file"), role="button"),
            tabindex=0,
            _class="bx--btn bx--btn--primary",
            data_file_drop_container=True,
            disabled=inputelement_attrs.get("disabled"),
            data_invalid=error_element.condition,
            _for=inputelement_attrs.get("id"),
        )
        input = self.get_input_element(
            inputelement_attrs,
            error_element,
            onload="""
document.addEventListener('change', (e) => {
    this.parentElement.querySelector('[data-file-container]').innerHTML = '';
    var widget = new CarbonComponents.FileUploader(this.parentElement);
    widget._displayFilenames();
    widget.setState('edit');
});
""",
        )
        clearbutton = hg.If(
            self.clearable,
            hg.SPAN(
                hg.BUTTON(
                    Icon("close", size=16),
                    _class="bx--file-close",
                    type="button",
                    aria_label="close",
                ),
                data_for=inputelement_attrs.get("id"),
                _class="bx--file__state-container",
            ),
        )
        super().__init__(
            hg.STRONG(_class="bx--file--label"),
            hg.P(_class="bx--label-description"),
            hg.DIV(
                uploadbutton,
                input,
                hg.DIV(
                    hg.If(
                        inputelement_attrs.get("value"),
                        hg.SPAN(
                            hg.P(
                                hg.A(
                                    hg.F(
                                        lambda c: os.path.basename(
                                            hg.resolve_lazy(inputelement_attrs, c).get(
                                                "value"
                                            )
                                        )
                                    ),
                                    href=hg.F(
                                        lambda c: settings.MEDIA_URL
                                        + hg.resolve_lazy(inputelement_attrs, c).get(
                                            "value"
                                        )
                                    ),
                                ),
                                _class="bx--file-filename",
                            ),
                            clearbutton,
                            _class="bx--file__selected-file",
                        ),
                    ),
                    data_file_container=True,
                    _class="bx--file-container",
                ),
                help_text_element,
                error_element,
                _class="bx--file",
                data_file=True,
            ),
            **attributes,
        )


class ClearableFileInput(BaseWidget):
    django_widget = widgets.ClearableFileInput
    clearable = True


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


def _combine_lazy_dict(attrs1, attrs2):
    return hg.F(
        lambda c: {
            **(hg.resolve_lazy(attrs1, c) or {}),
            **(hg.resolve_lazy(attrs2, c) or {}),
        }
    )


def _gen_optgroup(boundfield):
    def wrapper(context):
        bfield = hg.resolve_lazy(boundfield, context)
        return bfield.field.widget.optgroups(
            bfield.name,
            bfield.field.widget.format_value(bfield.value()),
        )

    return hg.F(wrapper)
