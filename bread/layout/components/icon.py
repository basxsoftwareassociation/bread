import logging
import os

import htmlgenerator as hg
from django.contrib.staticfiles import finders
from django.core.cache import cache
from django.utils.html import mark_safe

logger = logging.getLogger(__name__)


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
        super().__init__(**attributes)

    def render(self, context):
        name = hg.resolve_lazy(self.name, context)
        if cache.get(name) is None:
            path = finders.find(
                os.path.join("design/carbon_design/icons/flat/raw_32/", f"{name}.svg")
            )
            if not path:
                logger.error(f"Missing icon: {name}.svg")
                self.append(f"Missing icon: {name}.svg")
                return super().render(context)
            with open(path) as f:
                cache.set(name, f.read())
        self.clear()
        self.append(mark_safe(cache.get(name)))
        return super().render(context)
