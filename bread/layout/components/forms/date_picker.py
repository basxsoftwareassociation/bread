import htmlgenerator as hg
from _strptime import TimeRE
from django.utils import formats

from ..icon import Icon
from .helpers import REQUIRED_LABEL, ErrorList, HelperText, Label


class DatePicker(hg.DIV):
    def __init__(
        self,
        fieldname,
        placeholder="",
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
                + (" bx--date-picker--short" if short else ""),
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


PHP_FORMAT_CHARACTERS = "dDjlNSwzWFmMntLoYyaABgGhHisuveIOPTZcrU"

# maps python format characters to PHP format characters
# hint: the #-sign of the python formatters is ommited for the keys
LETTER_MAPPING = {
    "a": "D",
    "A": "l",
    "w": "w",
    "d": "d",
    "b": "M",
    "B": "F",
    "m": "m",
    "y": "y",
    "Y": "Y",
    "H": "H",
    "I": "h",
    "p": "A",
    "M": "i",
    "S": "s",
    "f": "u",
    "z": "O",
    "Z": "e",
    "%": "%",
    "G": "o",
    "u": "N",
    "V": "W",
}


def to_php_formatstr(formatstr, format_key=None):
    """Maps a python datetime format string to a PHP format string

    This function is usefull because a lot of template/front-end code uses
    the PHP-format string, e.g. the date-filter of django.
    The following format specifiers are currently not supported:
    "%j", "%U", "%W", "%c", "%x", "%X"
    If formatstr is none, the format_key will be used to lookup default django format strings.
    """
    formatstr = " " + (formatstr or formats.get_format(format_key)[0])
    ret = []
    for i, c in enumerate(formatstr):
        if c == "%" or i == 0:
            continue

        if formatstr[i - 1] == "%":
            if c not in LETTER_MAPPING:
                raise ValueError(
                    f"Format letter %{c}  in format string {formatstr[1:]} is currently not supported to be converted to a PHP date-formatting string"
                )
            ret.append(LETTER_MAPPING[c])
        else:
            if c in PHP_FORMAT_CHARACTERS:
                ret.append("\\" + c)
            else:
                ret.append(c)
    return "".join(ret)
