import logging
import os

import htmlgenerator as hg
from django.contrib.staticfiles import finders
from django.utils.html import mark_safe

logger = logging.getLogger(__name__)

RAW_ICON_BASE_PATH = "design/carbon_design/icons/flat/raw_32/"
ABSOLUTE_PATH = finders.find(RAW_ICON_BASE_PATH)
ICONS = {}

for name in os.listdir(ABSOLUTE_PATH):
    iconpath = os.path.join(ABSOLUTE_PATH, name)
    if os.path.isfile(iconpath):
        with open(iconpath) as f:
            ICONS[name.replace(".svg", "")] = mark_safe(f.read())


class Icon(hg.SVG):

    """Insert the SVG for a carbon icon.
    See https://www.carbondesignsystem.com/guidelines/icons/library for a list of all icons.
    In order to see the name which should be passed to this template tag, click on "Download SVG"
    for an icon and use the filename without the attribte, e.g. "thunderstorm--severe"."""

    def __init__(
        self,
        name,
        size=None,
        **attributes,
    ):
        attributes["viewBox"] = "0 0 32 32"
        attributes["preserveAspectRatio"] = "xMidYMid meet"
        attributes["focusable"] = "false"
        attributes["style"] = attributes.get("style", "") + " will-change: transform;"
        if size is None:
            attributes["width"] = "32"
            attributes["height"] = "32"
        else:
            attributes["width"] = size
            attributes["height"] = size
        self.name = name
        super().__init__(hg.F(lambda c: ICONS[hg.resolve_lazy(name, c)]), **attributes)
