import htmlgenerator as hg
from _strptime import TimeRE
from django.utils import formats

from .datetimeformatstring import to_php_formatstr
from .helpers import REQUIRED_LABEL, ErrorList, HelperText, Label
from .icon import Icon


class DatePicker(hg.DIV):
    def __init__(
        self,
        fieldname,
        placeholder="",
        light=False,
        short=False,
        simple=False,
        widgetattributes={},
        boundfield=None,
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

        input = hg.INPUT(
            placeholder=placeholder,
            type="text",
            **widgetattributes,
        )
        self.input = input
        if not simple:
            input.attributes["data-date-picker-input"] = True
            input = hg.DIV(
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
            hg.DIV(
                hg.DIV(
                    Label(),
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

        if boundfield is not None:
            if boundfield.field.disabled:
                self.label.attributes["_class"] += " bx--label--disabled"
            self.label.attributes["_for"] = boundfield.id_for_label
            self.label.append(boundfield.label)
            if boundfield.field.required:
                self.label.append(REQUIRED_LABEL)

            dateformat = (
                boundfield.field.widget.format
                or formats.get_format(boundfield.field.widget.format_key)[0]
            )
            dateformat_widget = to_php_formatstr(
                boundfield.field.widget.format,
                boundfield.field.widget.format_key,
            )
            if self.simple:
                self.input.attributes["pattern"] = TimeRE().compile(dateformat).pattern
            else:
                self.input.attributes["data_date_format"] = dateformat_widget

            if boundfield.help_text:
                self[0][0].append(HelperText(boundfield.help_text))
            if boundfield.errors:
                self.input.attributes["data-invalid"] = True
                self[1].append(
                    Icon(
                        "warning--filled",
                        size=16,
                        _class="bx--text-input__invalid-icon",
                    )
                )
                self[0][0].append(ErrorList(boundfield.errors))
