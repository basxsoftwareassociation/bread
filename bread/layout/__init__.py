import importlib

from crispy_forms.layout import HTML  # noqa
from crispy_forms.utils import TEMPLATE_PACK

from .base import *  # noqa

mod = importlib.import_module(f"bread.layout.{TEMPLATE_PACK}")
globals().update(vars(mod))
