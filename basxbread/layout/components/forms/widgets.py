import os
import warnings
from typing import Optional

import django_countries.widgets
import django_filters
import htmlgenerator as hg
from _strptime import TimeRE
from django.conf import settings
from django.forms import widgets as djangowidgets
from django.urls import reverse
from django.utils import formats
from django.utils.translation import gettext_lazy as _
from phonenumber_field.formfields import PhoneNumberField

from basxbread.utils import get_all_subclasses

from ..button import Button
from ..icon import Icon
from ..tag import Tag
from .helpers import REQUIRED_LABEL, Label, to_php_formatstr

# Missing widget implementations:
# DateTimeInput


# A plain, largely unstyled input element
# It provides the basic structure for fields used
# in basxbread forms
class BaseWidget(hg.DIV):
    # used to mark that this class can be used in place of the according django widget or field
    # all basxbread widgets must have this if they should be used automatically to render form fields
    django_widget = None

    # default attributes which are used to create the input element in a standardized way for many inputs
    carbon_input_class: str = ""
    carbon_input_error_class: str = ""
    input_type: Optional[str] = None

    # __init__ of derived classes should support the following parameters
    # label: basxbread.layout.components.forms.utils.Label
    # help_text: Optional[Any]
    # errors: basxbread.layout.components.forms.utils.ErrorList
    #         ``hg.If(getattr(errors, "condition", None), ...`` can be used
    #         to render parts depending if there are errors
    # inputelement_attrs: Union[Lazy[dict], dict],
    # boundfield: Optional[django.forms.BoundField],

    def __init__(self, *args, **kwargs):
        # prevent rendering of any of the special kwargs we use in generate_formfield
        for param in [
            "label_element",
            "label",
            "help_text_element",
            "error_element",
            "inputelement_attrs",
            "boundfield",
        ]:
            if param in kwargs:
                raise Exception(
                    f"Widget {type(self)} tries to render parameter {param}"
                )
        super().__init__(*args, **kwargs)

    def get_input_element(self, inputelement_attrs, errors, **kwargs):
        return hg.INPUT(
            type=self.input_type,
            lazy_attributes=_combine_lazy_dict(
                _append_classes(
                    inputelement_attrs if inputelement_attrs is not None else {},
                    self.carbon_input_class,
                    hg.If(
                        getattr(errors, "condition", False),
                        self.carbon_input_error_class,
                    ),
                ),
                kwargs,
            ),
            data_invalid=hg.If(getattr(errors, "condition", False), True),
        )

    def with_fieldwrapper(self):
        return hg.DIV(self, _class="bx--form-item")


class HiddenInput(BaseWidget):
    django_widget = djangowidgets.HiddenInput
    input_type = "hidden"

    def __init__(
        self,
        label=None,
        help_text=None,
        errors=None,
        inputelement_attrs=None,
        boundfield=None,
        **attributes,
    ):
        super().__init__(self.get_input_element(inputelement_attrs, errors))


class TextInput(BaseWidget):
    django_widget = djangowidgets.TextInput
    carbon_input_class = "bx--text-input"
    carbon_input_error_class = "bx--text-input--invalid"
    input_type = "text"

    def __init__(
        self,
        label=None,
        help_text=None,
        errors=None,
        inputelement_attrs=None,
        boundfield=None,
        icon=None,
        **attributes,
    ):
        inputelement_attrs = (
            inputelement_attrs if inputelement_attrs is not None else {}
        )
        inputelement_attrs = hg.merge_html_attrs(
            inputelement_attrs, {"style": "padding-right: 2.5rem"}
        )
        super().__init__(
            label,
            hg.DIV(
                hg.If(
                    getattr(errors, "condition", None),
                    Icon(
                        "warning--filled",
                        size=16,
                        _class="bx--text-input__invalid-icon",
                    ),
                ),
                self.get_input_element(inputelement_attrs, errors),
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
                data_invalid=hg.If(getattr(errors, "condition", None), True),
            ),
            errors,
            help_text,
            **hg.merge_html_attrs(attributes, {"_class": "bx--text-input-wrapper"}),
        )


class PhoneNumberInput(TextInput):
    input_type = "tel"
    django_widget = PhoneNumberField

    def __init__(self, *args, **attributes):
        super().__init__(*args, icon="phone", **attributes)


class UrlInput(TextInput):
    django_widget = djangowidgets.URLInput
    input_type = "url"

    def __init__(self, *args, **attributes):
        super().__init__(*args, icon="link", **attributes)


class EmailInput(TextInput):
    django_widget = djangowidgets.EmailInput
    input_type = "email"

    def __init__(self, *args, **attributes):
        super().__init__(*args, icon="email", **attributes)


class NumberInput(BaseWidget):
    django_widget = djangowidgets.NumberInput
    input_type = "number"

    def __init__(
        self,
        label=None,
        help_text=None,
        errors=None,
        inputelement_attrs=None,
        boundfield=None,
        **attributes,
    ):
        inputelement_attrs = (
            inputelement_attrs if inputelement_attrs is not None else {}
        )
        super().__init__(
            label,
            hg.DIV(
                self.get_input_element(inputelement_attrs, errors),
                hg.DIV(
                    hg.BUTTON(
                        Icon("caret--up", size=16),
                        _class="bx--number__control-btn up-icon",
                        type="button",
                    ),
                    hg.BUTTON(
                        Icon("caret--down", size=16),
                        _class="bx--number__control-btn down-icon",
                        type="button",
                    ),
                    _class="bx--number__controls",
                ),
                _class="bx--number__input-wrapper",
            ),
            errors,
            help_text,
            data_numberinput=True,
            data_invalid=hg.If(errors.condition, True),
            **hg.merge_html_attrs(attributes, {"_class": "bx--number"}),
        )


class TimeInput(TextInput):
    django_widget = djangowidgets.TimeInput
    input_type = "time"


class PasswordInput(TextInput):
    django_widget = djangowidgets.PasswordInput
    carbon_input_class = "bx--password-input bx--text-input"
    carbon_input_error_class = "bx--text-input--invalid"
    input_type = "password"

    def __init__(
        self,
        label=None,
        help_text=None,
        errors=None,
        inputelement_attrs=None,
        boundfield=None,
        **attributes,
    ):
        inputelement_attrs = (
            inputelement_attrs if inputelement_attrs is not None else {}
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
            label=label,
            help_text=help_text,
            errors=errors,
            inputelement_attrs=_combine_lazy_dict(
                inputelement_attrs, {"data_toggle_password_visibility": True}
            ),
            icon=showhidebtn,
            **hg.merge_html_attrs(
                attributes,
                {"data_text_input": True, "_class": "bx--password-input-wrapper"},
            ),
        )


class Textarea(BaseWidget):
    django_widget = djangowidgets.Textarea
    carbon_input_class = "bx--text-area bx--text-area--v2"
    carbon_input_error_class = "bx--text-area--invalid"

    def __init__(
        self,
        label=None,
        help_text=None,
        errors=None,
        inputelement_attrs=None,
        boundfield=None,
        **attributes,
    ):
        inputelement_attrs = (
            inputelement_attrs if inputelement_attrs is not None else {}
        )
        super().__init__(
            label,
            hg.DIV(
                hg.If(
                    getattr(errors, "condition", None),
                    Icon(
                        "warning--filled",
                        size=16,
                        _class="bx--text-area__invalid-icon",
                    ),
                ),
                hg.TEXTAREA(
                    boundfield.value() if boundfield is not None else None,
                    lazy_attributes=_combine_lazy_dict(
                        _append_classes(
                            inputelement_attrs,
                            self.carbon_input_class,
                            hg.If(
                                getattr(errors, "condition", None),
                                self.carbon_input_error_class,
                            ),
                        ),
                        {"value": None},
                    ),
                ),
                _class="bx--text-area__wrapper",
                data_invalid=hg.If(getattr(errors, "condition", None), True),
            ),
            help_text,
            errors,
            **attributes,
        )


class Select(BaseWidget):
    django_widget = djangowidgets.Select
    carbon_input_class = "bx--select-input"

    def __init__(
        self,
        label=None,
        help_text=None,
        errors=None,
        inputelement_attrs=None,
        boundfield=None,
        inline=False,
        choices=None,  # for non-django-form select elements use this
        **attributes,
    ):
        inputelement_attrs = (
            inputelement_attrs if inputelement_attrs is not None else {}
        )
        select_wrapper = hg.DIV(
            hg.If(
                _more_choices_than(choices if choices else boundfield, 12),
                hg.BaseElement(
                    Icon(
                        "search",
                        size=16,
                        style="height: 2rem; width: 1rem; margin-right: 0.5rem; cursor: pointer;",
                        aria_hidden="true",
                        onclick="""
let searchElem = this.nextElementSibling;
let resultsElem = this.nextElementSibling.nextElementSibling;
let selectElem = this.nextElementSibling.nextElementSibling.nextElementSibling;
searchElem.classList.toggle('hidden')
resultsElem.classList.toggle('hidden')
selectElem.classList.toggle('hidden')

if(searchElem.classList.contains('hidden')) {
    selectElem.focus()
} else {
    searchElem.focus()
}
""",
                    ),
                    hg.INPUT(
                        _class="bx--select-input hidden",
                        style="",
                        placeholder=_("Type to search"),
                        onkeyup="""
let query = event.target.value.toLowerCase().split(' ').filter((term) => term.length > 0)
let resultsElem = this.nextElementSibling
resultsElem.innerHTML = ''
if(query.length == 0 || query.findIndex((term) => term.length >= 2) == -1) {
    return
}
let searchElem = this
let selectElem = this.nextElementSibling.nextElementSibling;
var resultList = []
for(let opt of selectElem.childNodes) {
    let content = opt.innerHTML.toLowerCase()
    if(query.findIndex((term) => content.includes(term)) != -1) {
        resultList.push($.create("div", {
            class: 'hoverable',
            style: {padding: "0.5rem"},
            value: opt.getAttribute('value'),
            contents: [opt.innerText],
            onclick: (e) => {
                selectElem.value = e.target.getAttribute('value')
                searchElem.classList.toggle('hidden')
                resultsElem.classList.toggle('hidden')
                selectElem.classList.toggle('hidden')
            },
            rank: searchMatchRank(query, opt.innerText)
        }))
    }
}
let sorted = resultList.sort((a, b) => parseFloat(a.getAttribute('rank')) > parseFloat(b.getAttribute('rank')) ? 1 : -1).slice(0, 10)
sorted.forEach(node => resultsElem.appendChild(node))
                """,
                    ),
                    hg.DIV(
                        _class="hidden",
                        style="position: absolute; height: auto; min-width: 5rem; min-height: 0.5rem; top: 2.5rem; z-index: 10; box-shadow: gray 0 3px 6px 3px; overflow-y: scroll; overflow-x: hidden; margin-left: 1.5rem",
                    ),
                ),
            ),
            hg.SELECT(
                hg.Iterator(
                    (
                        _optgroups_from_choices(
                            choices,
                            name=inputelement_attrs.get("name"),
                            value=inputelement_attrs.get("value"),
                        )
                        if choices
                        else _gen_optgroup(boundfield)
                    ),
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
                    inputelement_attrs,
                    self.carbon_input_class,
                    hg.If(
                        getattr(errors, "condition", None),
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
                getattr(errors, "condition", None),
                Icon(
                    "warning--filled",
                    size=16,
                    _class="bx--select__invalid-icon",
                ),
            ),
            _class="bx--select-input__wrapper",
            data_invalid=hg.If(getattr(errors, "condition", None), True),
        )
        super().__init__(
            label,
            hg.If(
                inline,
                hg.DIV(
                    select_wrapper,
                    errors,
                    _class="bx--select-input--inline__wrapper",
                ),
                select_wrapper,
            ),
            help_text,
            hg.If(inline, None, errors),  # not displayed if this is inline
            **hg.merge_html_attrs(
                attributes,
                {
                    "_class": hg.BaseElement(
                        "bx--select",
                        hg.If(inline, " bx--select--inline"),
                        hg.If(
                            getattr(errors, "condition", None), " bx--select--invalid"
                        ),
                        hg.If(
                            inputelement_attrs.get("disabled"),
                            " bx--select--disabled",
                        ),
                    ),
                },
            ),
        )


class NullBooleanSelect(Select):
    django_widget = djangowidgets.NullBooleanSelect


class SelectMultiple(BaseWidget):
    django_widget = djangowidgets.SelectMultiple

    def __init__(
        self,
        label=None,
        help_text=None,
        errors=None,
        inputelement_attrs=None,
        boundfield=None,  # for django-form select elements use this
        choices=None,  # for non-django-form select elements use this
        **attributes,  # for non-django-form select elements use this
    ):
        inputelement_attrs = (
            inputelement_attrs if inputelement_attrs is not None else {}
        )
        optgroups = (
            _optgroups_from_choices(
                choices,
                name=inputelement_attrs.get("name"),
                value=inputelement_attrs.get("value"),
            )
            if choices
            else _gen_optgroup(boundfield)
        )

        def countselected(context):
            options = [o for og in hg.resolve_lazy(optgroups, context) for o in og[1]]
            return len([o for o in options if o and o["selected"]])

        values = hg.UL(
            hg.Iterator(
                hg.F(
                    lambda c: hg.resolve_lazy(boundfield, c).field.to_python(
                        hg.resolve_lazy(boundfield, c).value()
                    )
                ),
                "value",
                hg.LI(Tag(hg.C("value"))),
            ),
        )

        super().__init__(
            label,
            hg.If(
                inputelement_attrs.get("disabled"),
                hg.DIV(
                    hg.Iterator(
                        optgroups,
                        "optiongroup",
                        hg.Iterator(
                            hg.C("optiongroup.1"),
                            "option",
                            hg.If(hg.C("option.selected"), Tag(hg.C("option.label"))),
                        ),
                    ),
                ),
                hg.DIV(
                    hg.DIV(
                        hg.DIV(
                            hg.F(countselected),
                            Icon(
                                "close",
                                focusable="false",
                                size=15,
                                role="img",
                                onclick="clearMultiselect(this.parentElement.parentElement.parentElement)",
                            ),
                            role="button",
                            _class="bx--list-box__selection bx--list-box__selection--multi bx--tag--filter",
                            tabindex="0",
                            title="Clear all selected items",
                        ),
                        hg.INPUT(
                            _class="bx--text-input",
                            placeholder="Filter...",
                            onclick="this.parentElement.nextElementSibling.style.display = 'block'",
                            onkeyup="filterOptions(this.parentElement.parentElement)",
                        ),
                        hg.DIV(
                            Icon(
                                "chevron--down", size=16, role="img", focusable="false"
                            ),
                            _class="bx--list-box__menu-icon",
                            onclick="this.parentElement.nextElementSibling.style.display = this.parentElement.nextElementSibling.style.display == 'none' ? 'block' : 'none';",
                        ),
                        role="button",
                        _class="bx--list-box__field",
                        tabindex="0",
                        onload="window.addEventListener('click', (e) => {this.nextElementSibling.style.display = 'none'})",
                    ),
                    hg.FIELDSET(
                        hg.Iterator(
                            optgroups,
                            "optgroup",
                            hg.Iterator(
                                hg.C("optgroup.1"),
                                "option",
                                hg.DIV(
                                    hg.DIV(
                                        hg.DIV(
                                            hg.LABEL(
                                                hg.INPUT(
                                                    type="checkbox",
                                                    readonly=True,
                                                    _class="bx--checkbox",
                                                    value=hg.C("option.value"),
                                                    lazy_attributes=hg.C(
                                                        "option.attrs"
                                                    ),
                                                    onchange="updateMultiselect(this.closest('.bx--multi-select'))",
                                                    checked=hg.C("option.selected"),
                                                    name=hg.C("option.name"),
                                                ),
                                                hg.SPAN(
                                                    _class="bx--checkbox-appearance"
                                                ),
                                                hg.SPAN(
                                                    hg.C("option.label"),
                                                    _class="bx--checkbox-label-text",
                                                ),
                                                title=hg.C("option.label"),
                                                _class="bx--checkbox-label",
                                            ),
                                            _class="bx--form-item bx--checkbox-wrapper",
                                        ),
                                        _class="bx--list-box__menu-item__option",
                                    ),
                                    _class="bx--list-box__menu-item",
                                ),
                            ),
                        ),
                        _class="bx--list-box__menu",
                        role="listbox",
                        style="display: none",
                    ),
                    _class=hg.BaseElement(
                        "bx--multi-select bx--list-box bx--multi-select--selected bx--combo-box bx--multi-select--filterable",
                        hg.If(
                            inputelement_attrs.get("disabled"),
                            " bx--list-box--disabled",
                        ),
                    ),
                    data_invalid=hg.If(getattr(errors, "condition", None), True),
                ),
            ),
            help_text,
            values,
            errors,
            **hg.merge_html_attrs(
                attributes,
                {
                    "onclick": "event.stopPropagation()",
                    "_class": "bx--list-box__wrapper",
                },
            ),
        )


class Checkbox(BaseWidget):
    django_widget = djangowidgets.CheckboxInput
    carbon_input_class = "bx--checkbox"
    input_type = "checkbox"

    def __init__(
        self,
        label=None,
        help_text=None,
        errors=None,
        inputelement_attrs=None,
        boundfield=None,
        **attributes,
    ):
        inputelement_attrs = (
            inputelement_attrs if inputelement_attrs is not None else {}
        )
        attrs = {}
        if boundfield is not None:
            attrs["checked"] = hg.F(
                lambda c: hg.resolve_lazy(boundfield, c).field.widget.check_test(
                    hg.resolve_lazy(boundfield, c).value()
                )
            )
            attrs["value"] = None
        inputelement_attrs = _combine_lazy_dict(inputelement_attrs, attrs)
        # labels for checkboxes are treated a bit different, need to use plain value
        label = hg.F(
            lambda c, label=label: getattr(hg.resolve_lazy(label, c), "label", label)
        )
        required = hg.F(lambda c, label=label: hg.resolve_lazy(label, c) is not None)
        super().__init__(
            hg.LABEL(
                self.get_input_element(inputelement_attrs, errors),
                label,
                hg.If(
                    inputelement_attrs.get("required"), hg.If(required, REQUIRED_LABEL)
                ),
                _class=hg.BaseElement(
                    "bx--checkbox-label",
                    hg.If(inputelement_attrs.get("disabled"), " bx--label--disabled"),
                ),
                data_contained_checkbox_state=hg.If(
                    inputelement_attrs.get("checked"),
                    "true",
                    "false",
                ),
                data_invalid=hg.If(getattr(errors, "condition", False), True),
            ),
            help_text,
            errors,
            **hg.merge_html_attrs(attributes, {"_class": "bx--checkbox-wrapper"}),
        )


class CheckboxSelectMultiple(BaseWidget):
    django_widget = djangowidgets.CheckboxSelectMultiple
    carbon_input_class = "bx--checkbox"
    input_type = "checkbox"

    def __init__(
        self,
        label=None,
        help_text=None,
        errors=None,
        inputelement_attrs=None,
        boundfield=None,
        **attributes,
    ):
        inputelement_attrs = (
            inputelement_attrs if inputelement_attrs is not None else {}
        )
        super().__init__(
            hg.FIELDSET(
                label,
                hg.Iterator(
                    boundfield.subwidgets,
                    "checkbox",
                    Checkbox(
                        label=Label(hg.C("checkbox").data["label"]),
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
                ),
                data_invalid=hg.If(getattr(errors, "condition", False), True),
            ),
            help_text,
            errors,
            **attributes,
        )


class RadioButton(BaseWidget):
    django_widget = None  # only used inside RadioSelect
    carbon_input_class = "bx--radio-button"
    input_type = "radio"

    def __init__(
        self,
        label=None,
        help_text=None,
        errors=None,
        inputelement_attrs=None,
        boundfield=None,
        **attributes,
    ):
        inputelement_attrs = (
            inputelement_attrs if inputelement_attrs is not None else {}
        )
        attrs = {}
        if boundfield is not None:
            attrs["checked"] = hg.F(
                lambda c: hg.resolve_lazy(boundfield, c).field.widget.check_test(
                    hg.resolve_lazy(boundfield, c).value()
                )
            )
        inputelement_attrs = _combine_lazy_dict(inputelement_attrs, attrs)
        label = None if label is None else label.label
        super().__init__(
            self.get_input_element(inputelement_attrs, errors),
            hg.LABEL(
                hg.SPAN(_class="bx--radio-button__appearance"),
                hg.SPAN(label, _class="bx--radio-button__label-text"),
                _class="bx--radio-button__label",
                _for=inputelement_attrs.get("id"),
            ),
            help_text,
            errors,
            **hg.merge_html_attrs(attributes, {"_class": "bx--radio-button-wrapper"}),
        )


class RadioSelect(BaseWidget):
    django_widget = djangowidgets.RadioSelect
    carbon_input_class = "bx--radio-button"
    input_type = "radio"

    def __init__(
        self,
        label=None,
        help_text=None,
        errors=None,
        inputelement_attrs=None,
        boundfield=None,
        **attributes,
    ):
        inputelement_attrs = (
            inputelement_attrs if inputelement_attrs is not None else {}
        )
        super().__init__(
            hg.FIELDSET(
                label,
                hg.DIV(
                    hg.Iterator(
                        boundfield.subwidgets,
                        "radiobutton",
                        RadioButton(
                            label=Label(hg.C("radiobutton").data["label"]),
                            inputelement_attrs=_combine_lazy_dict(
                                _combine_lazy_dict(
                                    inputelement_attrs,
                                    {
                                        "name": hg.C("radiobutton").data["name"],
                                        "value": hg.C("radiobutton").data["value"],
                                        "checked": hg.C("radiobutton").data["selected"],
                                    },
                                ),
                                hg.C("radiobutton").data["attrs"],
                            ),
                        ),
                    ),
                    _class="bx--radio-button-group  bx--radio-button-group--vertical",
                ),
                data_invalid=hg.If(getattr(errors, "condition", False), True),
            ),
            help_text,
            errors,
            **attributes,
        )


class DatePicker(BaseWidget):
    django_widget = djangowidgets.DateInput
    carbon_input_class = "bx--date-picker__input"
    input_type = "text"  # prevent browser style date picker but use carbon design

    def __init__(
        self,
        label=None,
        help_text=None,
        errors=None,
        inputelement_attrs=None,
        boundfield=None,
        style_short=False,
        style_simple=False,
        format=None,
        formatkey=None,
        **attributes,
    ):
        inputelement_attrs = (
            inputelement_attrs if inputelement_attrs is not None else {}
        )

        def format_date_value(context):
            bfield = hg.resolve_lazy(boundfield, context)
            return bfield.field.widget.format_value(bfield.value())

        super().__init__(
            hg.DIV(
                label,
                hg.If(
                    style_simple,
                    self.get_input_element(
                        inputelement_attrs,
                        errors,
                        data_invalid=hg.If(getattr(errors, "condition", False), True),
                        pattern=hg.F(
                            lambda c: (
                                TimeRE()
                                .compile(
                                    format
                                    or hg.resolve_lazy(
                                        boundfield, c
                                    ).field.widget.format
                                    or formats.get_format(
                                        formatkey
                                        or hg.resolve_lazy(
                                            boundfield, c
                                        ).field.widget.format_key
                                    )[0]
                                )
                                .pattern
                            )
                        ),
                        value=hg.F(format_date_value),
                    ),
                    hg.DIV(
                        self.get_input_element(
                            inputelement_attrs,
                            errors,
                            data_date_picker_input=True,
                            data_invalid=hg.If(
                                getattr(errors, "condition", False), True
                            ),
                            data_date_format=hg.F(
                                lambda c: to_php_formatstr(
                                    format
                                    or getattr(
                                        hg.resolve_lazy(boundfield, c).field.widget,
                                        "format",
                                        None,
                                    ),
                                    formatkey
                                    or hg.resolve_lazy(
                                        boundfield, c
                                    ).field.widget.format_key,
                                )
                            ),
                            value=hg.F(format_date_value),
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
                help_text,
                errors,
                _class="bx--date-picker-container",
            ),
            **hg.merge_html_attrs(
                attributes,
                {
                    "data_date_picker": not style_simple,
                    "data_date_picker_type": None if style_simple else "single",
                    "_class": hg.BaseElement(
                        "bx--date-picker",
                        hg.If(
                            style_simple,
                            " bx--date-picker--simple",
                            " bx--date-picker--single",
                        ),
                        hg.If(style_short, " bx--date-picker--short"),
                    ),
                },
            ),
        )


class FileInput(BaseWidget):
    django_widget = djangowidgets.FileInput
    carbon_input_class = "bx--file-input bx--visually-hidden"
    input_type = "file"
    clearable = False

    def __init__(
        self,
        label=None,
        help_text=None,
        errors=None,
        inputelement_attrs=None,
        boundfield=None,
        **attributes,
    ):
        inputelement_attrs = (
            inputelement_attrs if inputelement_attrs is not None else {}
        )
        uploadbutton = hg.LABEL(
            hg.SPAN(
                hg.If(inputelement_attrs.get("value"), "...", _("Select file")),
                role="button",
            ),
            tabindex=0,
            _class=hg.BaseElement(
                "bx--btn bx--btn--tertiary",
                hg.If(inputelement_attrs.get("disabled"), " bx--btn--disabled"),
            ),
            data_file_drop_container=True,
            disabled=inputelement_attrs.get("disabled"),
            data_invalid=hg.If(getattr(errors, "condition", False), True),
            _for=inputelement_attrs.get("id"),
        )
        input = self.get_input_element(
            inputelement_attrs,
            errors,
            onload="""
that = this;
document.addEventListener('change', (e) => {
    that.parentElement.querySelector('[data-file-container]').innerHTML = '';
    var widget = new CarbonComponents.FileUploader(that.parentElement);
    widget._displayFilenames();
    widget.setState('edit');
});
""",
        )
        # we can only clear the field if it originates form a django field
        # otherwise it has no use
        clearbox = None
        if boundfield is not None:
            checkbox_name = hg.F(
                lambda c: hg.resolve_lazy(
                    boundfield, c
                ).field.widget.clear_checkbox_name(
                    hg.resolve_lazy(boundfield, c).html_name
                )
            )
            checkbox_id = hg.F(
                lambda c: hg.resolve_lazy(boundfield, c).field.widget.clear_checkbox_id(
                    hg.resolve_lazy(checkbox_name, c)
                )
            )
            clearbox = hg.If(
                self.clearable,
                hg.INPUT(
                    type="checkbox",
                    name=checkbox_name,
                    id=checkbox_id,
                    style="display: none",
                ),
            )

        # clearbutton is always used, to allow clearing a just selected field in the browser
        clearbutton = hg.If(
            self.clearable,
            hg.SPAN(
                hg.BUTTON(
                    Icon("close", size=16),
                    _class="bx--file-close",
                    type="button",
                    aria_label="close",
                    onclick=hg.If(
                        clearbox,
                        hg.format("$('#{}').checked = 'checked';", checkbox_id),
                    ),
                ),
                data_for=inputelement_attrs.get("id"),
                _class="bx--file__state-container",
            ),
        )

        super().__init__(
            label,
            hg.DIV(
                uploadbutton,
                input,
                clearbox,
                hg.DIV(
                    hg.If(
                        inputelement_attrs.get("value"),
                        hg.SPAN(
                            hg.P(
                                hg.If(
                                    hg.F(
                                        lambda c: hasattr(
                                            hg.resolve_lazy(inputelement_attrs, c)
                                            .get("value")
                                            .file,
                                            "name",
                                        )
                                    ),
                                    hg.A(
                                        hg.F(
                                            lambda c: os.path.basename(
                                                hg.resolve_lazy(inputelement_attrs, c)
                                                .get("value")
                                                .name
                                            )
                                        ),
                                        href=hg.F(
                                            lambda c: settings.MEDIA_URL
                                            + hg.resolve_lazy(inputelement_attrs, c)
                                            .get("value")
                                            .name
                                        ),
                                    ),
                                    hg.F(
                                        lambda c: os.path.basename(
                                            hg.resolve_lazy(inputelement_attrs, c)
                                            .get("value")
                                            .name
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
                help_text,
                errors,
                _class="bx--file",
                data_file=True,
            ),
            **attributes,
        )


class ClearableFileInput(FileInput):
    django_widget = djangowidgets.ClearableFileInput
    clearable = True


class LazySelect(Select):
    django_widget = django_countries.widgets.LazySelect


class AjaxSearchWidget(BaseWidget):
    carbon_input_error_class = "bx--text-input--invalid"

    def __init__(
        self,
        label=None,
        help_text=None,
        errors=None,
        inputelement_attrs=None,
        boundfield=None,
        **attributes,
    ):
        inputelement_attrs = (
            inputelement_attrs if inputelement_attrs is not None else {}
        )
        searchresult_id = hg.format("{}-searchresult", inputelement_attrs.get("id"))
        super().__init__(
            label,
            hg.DIV(
                hg.If(
                    getattr(errors, "condition", None),
                    Icon(
                        "warning--filled",
                        size=16,
                        _class="bx--text-input__invalid-icon",
                    ),
                ),
                hg.DIV(
                    _("Loading..."),
                    id=hg.format("{}-loader", inputelement_attrs.get("id")),
                    _class="htmx-indicator",
                    style="position: absolute;z-index: 1;right: 8px; pointer-events: none",
                ),
                hg.INPUT(type="hidden", lazy_attributes=inputelement_attrs),
                hg.INPUT(
                    _class=hg.BaseElement(
                        "bx--text-input bread-ajax-search",
                        hg.If(
                            getattr(errors, "condition", False),
                            " bx--text-input--invalid",
                        ),
                    ),
                    data_invalid=hg.If(getattr(errors, "condition", False), True),
                    name="query",
                    type="text",
                    hx_get=reverse(self.url),
                    hx_trigger="input changed delay:100ms",
                    hx_target=hg.format("#{}", searchresult_id),
                    hx_indicator=hg.format("#{}-loader", inputelement_attrs.get("id")),
                    onfocusin="this.parentElement.nextElementSibling.nextElementSibling.style.display = 'block'",
                    style="padding-right: 2.5rem",
                ),
                _class="bx--text-input__field-wrapper",
                data_invalid=hg.If(getattr(errors, "condition", None), True),
            ),
            Tag(
                hg.F(
                    lambda c: type(self).formatter(
                        hg.resolve_lazy(boundfield, c).field.to_python(
                            hg.resolve_lazy(boundfield, c).value()
                        )
                    )
                ),
                can_delete=hg.F(
                    lambda c: not hg.resolve_lazy(boundfield, c).field.required
                ),
                style=hg.If(
                    hg.F(lambda c: not hg.resolve_lazy(boundfield, c).value()),
                    "display: none",
                ),
                ondelete=hg.format(
                    """document.getElementById('{}').value = ''; this.parentElement.style.display = 'none'""",
                    inputelement_attrs.get("id"),
                ),
            ),
            hg.DIV(
                hg.SPAN("...", style="padding: 8px"),
                id=searchresult_id,
                style="border-left: solid 1px gray; border-right: solid 1px gray; border-bottom: solid 1px gray; background: white; z-index: 99; display: none",
            ),
            errors,
            help_text,
            **hg.merge_html_attrs(attributes, {"_class": "bx--text-input-wrapper"}),
        )


def AjaxSearch(url, formatter=str):
    return type(
        "SubclassedAjaxSearchWidget",
        (AjaxSearchWidget,),
        {"url": url, "formatter": formatter},
    )


class MultiWidget(BaseWidget):
    django_widget = djangowidgets.MultiWidget

    def __init__(
        self,
        label=None,
        help_text=None,
        errors=None,
        inputelement_attrs=None,
        boundfield=None,
        **attributes,
    ):
        def _subwidgets(context):
            ret = []
            if boundfield is not None:
                realboundfield = hg.resolve_lazy(boundfield, context)
                for i, (widget, data) in enumerate(
                    zip(
                        realboundfield.subwidgets[0].parent_widget.widgets,
                        realboundfield.subwidgets[0].data["subwidgets"],
                    )
                ):
                    # required because bread uses _class instead of "class"
                    # otherwise "class" will override "_class" when rendering
                    if "class" in data["attrs"]:
                        data = dict(data)
                        data["attrs"]["_class"] = data["attrs"]["class"]
                        del data["attrs"]["class"]
                    ret.append(self.subwidget(realboundfield, widget, data, i))
            return hg.DIV(*ret)

        super().__init__(label, help_text, errors, hg.F(_subwidgets), **attributes)

    def subwidget(self, boundfield, djangowidget, djangodata, i):
        widgetclass = django2bread_widgetclass(type(djangowidget))
        return widgetclass(
            label=None,
            help_text=None,
            errors=None,
            inputelement_attrs={
                "name": djangodata["name"],
                "value": djangodata["value"],
                "required": djangodata["required"],
                **djangodata["attrs"],
            },
            boundfield=boundfield,
        )


class SplitDateTimeWidget(MultiWidget):
    django_widget = djangowidgets.SplitDateTimeWidget

    def subwidget(self, boundfield, djangowidget, djangodata, i):
        if isinstance(djangowidget, djangowidgets.DateInput):
            return DatePicker(
                label=None,
                help_text=None,
                errors=None,
                inputelement_attrs={
                    "name": djangodata["name"],
                    "value": djangodata["value"],
                    "required": djangodata["required"],
                    **djangodata["attrs"],
                },
                boundfield=boundfield,
                format=djangowidget.format,
                formatkey=djangowidget.format_key,
            )
        return super().subwidget(boundfield, djangowidget, djangodata, i)


class DateRangeWidget(MultiWidget):
    django_widget = django_filters.widgets.DateRangeWidget

    def subwidget(self, boundfield, djangowidget, djangodata, i):
        labelmap = {0: _("From"), 1: _("To")}
        return DatePicker(
            label=Label(labelmap[i]),
            help_text=None,
            errors=None,
            inputelement_attrs={
                "name": djangodata["name"],
                "value": djangodata["value"],
                "required": djangodata["required"],
                "style": "max-width: 8rem;",
                **djangodata["attrs"],
            },
            boundfield=boundfield,
            formatkey="DATE_INPUT_FORMATS",
            style="padding-left: 2rem",
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


def _combine_lazy_dict(attrs1, attrs2):
    return hg.F(
        lambda c: {
            **(hg.resolve_lazy(attrs1, c) or {}),
            **(hg.resolve_lazy(attrs2, c) or {}),
        }
    )


def _flat_count(choices):
    count = 0
    for key, value in choices:
        if isinstance(value, (list, tuple)):
            count += len(value)
        else:
            count += 1
    return count


def _more_choices_than(choices, count):
    if isinstance(choices, hg.Lazy):

        def wrapper(context):
            bfield = hg.resolve_lazy(choices, context)
            return _flat_count(bfield.field.widget.choices) > count

        return hg.F(wrapper)
    else:
        return _flat_count(choices) > count


def _gen_optgroup(boundfield):
    def wrapper(context):
        bfield = hg.resolve_lazy(boundfield, context)
        return bfield.field.widget.optgroups(
            bfield.html_name,
            bfield.field.widget.format_value(bfield.value()),
        )

    return hg.F(wrapper)


# based on https://github.com/django/django/blob/c6c6cd3c5ad9c36795bb120e521590424f034ae4/django/forms/widgets.py#L587
def _optgroups_from_choices(optchoices, name, value):
    groups = []

    for index, (option_value, option_label) in enumerate(optchoices):
        if option_value is None:
            option_value = ""

        subgroup = []
        if isinstance(option_label, (list, tuple)):
            group_name = option_value
            subindex = 0
            choices = option_label
        else:
            group_name = None
            subindex = None
            choices = [(option_value, option_label)]
        groups.append((group_name, subgroup, index))

        for subvalue, sublabel in choices:
            selected = hg.F(
                lambda c, v=subvalue: hg.resolve_lazy(v, c) == hg.resolve_lazy(value, c)
            )
            subgroup.append(
                {
                    "name": name,
                    "value": subvalue,
                    "label": sublabel,
                    "selected": selected,
                    "attrs": {
                        "selected": selected,
                    },
                }
            )
            if subindex is not None:
                subindex += 1
    return groups


def django2bread_widgetclass(widgetclass, fieldclass=None) -> Optional[hg.Lazy]:
    if django2bread_widgetclass.widget_map is None:  # type: ignore

        django2bread_widgetclass.widget_map: dict = {}  # type: ignore
        for cls in get_all_subclasses(BaseWidget):
            if cls.django_widget not in django2bread_widgetclass.widget_map:  # type: ignore
                django2bread_widgetclass.widget_map[cls.django_widget] = []  # type: ignore
            django2bread_widgetclass.widget_map[cls.django_widget].append(cls)  # type: ignore
        for key, widgetclasses in django2bread_widgetclass.widget_map.items():  # type: ignore
            if key is not None and len(widgetclasses) > 1:
                warnings.warn(
                    "There are more than one basxbread widget implementations "
                    f"available for the django widget {key}: {widgetclasses}"
                )

    # the fieldclass is rarelly used to register something, but a few 3rd
    # party fields can only be distinguished this way, e.g.
    # django-phonenumber-field
    if fieldclass is not None and fieldclass in django2bread_widgetclass.widget_map:  # type: ignore
        return django2bread_widgetclass.widget_map[fieldclass][0]  # type: ignore
    for widgetbaseclass in widgetclass.mro():
        if widgetbaseclass in django2bread_widgetclass.widget_map:  # type: ignore
            return django2bread_widgetclass.widget_map[widgetbaseclass][0]  # type: ignore
    warnings.warn(
        f"Form field {fieldclass} uses widget {widgetclass} but "
        "basxbread has no implementation, will default to TextInput"
    )
    return None


django2bread_widgetclass.widget_map: Optional[dict] = None  # type: ignore
