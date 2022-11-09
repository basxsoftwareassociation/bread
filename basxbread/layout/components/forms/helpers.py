import htmlgenerator as hg
from django.conf import settings
from django.utils import formats
from django.utils.translation import gettext_lazy as _

from ..button import Button

REQUIRED_LABEL = getattr(settings, "REQUIRED_LABEL", " *")


class Submit(hg.DIV):
    def __init__(self, label=None, name="submit", **attributes):
        super().__init__(
            Button(label or _("Save"), type="submit", name=name),
            _class="bx--form-item",
            **attributes,
        )


class Label(hg.If):
    def __init__(self, label, _for=None, required=None, disabled=None, **kwargs):
        self.label = label
        super().__init__(
            label,
            hg.LABEL(
                label,
                hg.If(required, REQUIRED_LABEL),
                _for=_for,
                _class=hg.BaseElement(
                    "bx--label",
                    hg.If(disabled, " bx--label--disabled"),
                ),
                **kwargs,
            ),
        )


class HelpText(hg.If):
    def __init__(self, helptext, disabled=False):
        super().__init__(
            helptext,
            hg.DIV(
                helptext,
                _class=hg.BaseElement(
                    "bx--form__helper-text",
                    hg.If(disabled, " bx--form__helper-text--disabled"),
                ),
            ),
        )


class ErrorList(hg.If):
    def __init__(self, errors):
        super().__init__(
            errors,
            hg.DIV(
                hg.UL(hg.Iterator(errors or (), "error", hg.LI(hg.C("error")))),
                _class="bx--form-requirement",
            ),
        )


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
