#!/usr/bin/env python
"""
To regenerate that module to contain the latest list of  IANA Language
Subtag Registry, either call this module directly from the command line
(``python regenenerate.py``), or call the ``regenerate`` method.

"""
import os
import re
import urllib
import urllib.request

TEMPLATE = """from django.utils.translation import gettext as _

LANGUAGES = (
    %(languages)s
)

"""


def regenerate():
    """
    Generate the languages Python module.
    """
    paren = re.compile(r"\([^)]*\)")
    location = "http://www.iana.org/assignments/language-subtag-registry"

    # Get the language list.
    with urllib.request.urlopen(location) as f:  # nosec # because hardcoded
        lines = f.read().decode().splitlines()
    languages = []
    info = {}
    p = None
    for line in lines:
        if line == "%%":
            if (
                "Type" in info
                and info["Type"] == "language"
                and info["Description"] != "Private use"
            ):
                languages.append(info)
            info = {}
        elif ":" not in line and p:
            info[p[0]] = paren.sub("", p[2] + line).strip()
        else:
            p = line.partition(":")
            if (
                not p[0] in info
            ):  # Keep the first description as it should be the most common
                info[p[0]] = paren.sub("", p[2]).strip()

    languages_lines = map(
        lambda x: '("%s", _(u"%s")),' % (x["Subtag"], x["Description"]), languages
    )

    # Generate and save the file.
    filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "languages.py")
    # TODO: first make a backup of the file if it exists already.
    with open(filename, "w") as f:
        f.write(
            TEMPLATE
            % {
                "languages": "\n    ".join(languages_lines),
            }
        )


if __name__ == "__main__":
    regenerate()
