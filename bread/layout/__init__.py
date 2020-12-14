from htmlgenerator import *  # noqa

from . import components  # noqa
from .base import *  # noqa
from .components import (  # noqa
    button,
    datatable,
    form,
    grid,
    icon,
    notification,
    overflow_menu,
    progress_indicator,
    search,
)

"""A layout-object is a callable which accepts a request object as single parameter and returns an element tree"""


def elementtree_as_layout(element):
    """A simple wrapper to convert an element tree into a layout object"""
    return lambda request: element
