from .export import *  # noqa
from .media import *  # noqa
from .model_helpers import *  # noqa
from .views import *  # noqa


def try_call(var, *args, **kwargs):
    return var(*args, **kwargs) if callable(var) else var
