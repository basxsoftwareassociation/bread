from _strptime import TimeRE

import htmlgenerator
from bread.utils.datetimeformatstring import to_php_formatstr
from django.utils import formats
from django.utils.translation import gettext as _

from .form import ErrorList, HelperText
from .icon import Icon


class DatePicker(htmlgenerator.DIV):
    def __init__(
        self,
        fieldname,
        placeholder="",
        light=False,
        short=False,
        simple=False,
        widgetattributes={},
        **attributes,
    ):
        self.fieldname = fieldname
        attributes["_class"] = attributes.get("_class", "") + " bx--form-item"
        picker_attribs = (
            {}
            if simple
            else {"data-date-picker": True, "data-date-picker-type": "single"}
        )
        widgetattributes["_class"] = (
            widgetattributes.get("_class", "") + " bx--date-picker__input"
        )

        input = htmlgenerator.INPUT(
            placeholder=placeholder,
            type="text",
            **widgetattributes,
        )
        self.input = input
        if not simple:
            input.attributes["data-date-picker-input"] = True
            input = htmlgenerator.DIV(
                input,
                Icon(
                    "calendar",
                    size=16,
                    _class="bx--date-picker__icon",
                    data_date_picker_icon="true",
                ),
                _class="bx--date-picker-input__wrapper",
            )

        super().__init__(
            htmlgenerator.DIV(
                htmlgenerator.DIV(
                    htmlgenerator.LABEL(_class="bx--label"),
                    input,
                    _class="bx--date-picker-container",
                ),
                _class="bx--date-picker"
                + (" bx--date-picker--simple" if simple else "bx--date-picker--single")
                + (" bx--date-picker--short" if short else "")
                + (" bx--date-picker--light" if light else ""),
                **picker_attribs,
            ),
            **attributes,
        )
        # for easier reference in the render method:
        self.label = self[0][0][0]
        self.simple = simple

    def render(self, context):
        if self.boundfield is not None:
            if self.boundfield.field.disabled:
                self.label.attributes["_class"] += " bx--label--disabled"
            self.label.attributes["_for"] = self.boundfield.id_for_label
            self.label.append(self.boundfield.label)
            if not self.boundfield.field.required:
                self.label.append(_(" (optional)"))

            dateformat = (
                self.boundfield.field.widget.format
                or formats.get_format(self.boundfield.field.widget.format_key)[0]
            )
            dateformat_widget = to_php_formatstr(
                self.boundfield.field.widget.format,
                self.boundfield.field.widget.format_key,
            )
            if self.simple:
                self.input.attributes["pattern"] = TimeRE().compile(dateformat).pattern
            else:
                self.input.attributes["data_date_format"] = dateformat_widget

            if self.boundfield.help_text:
                self[0][0].append(HelperText(self.boundfield.help_text))
            if self.boundfield.errors:
                self.input.attributes["data-invalid"] = True
                self[1].append(
                    Icon(
                        "warning--filled",
                        size=16,
                        _class="bx--text-input__invalid-icon",
                    )
                )
                self[0][0].append(ErrorList(self.boundfield.errors))
        return super().render(context)
