from django.utils import formats

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
