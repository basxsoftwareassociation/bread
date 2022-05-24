from django.conf import settings
from django.http import HttpResponse
from django.template.context import _builtin_context_processors
from django.utils.module_loading import import_string

from . import components  # noqa
from .componentpreview import *  # noqa
from .components import *  # noqa
from .components import button  # noqa
from .components import content_switcher  # noqa
from .components import datatable  # noqa
from .components import fieldexplorer  # noqa
from .components import forms  # noqa
from .components import grid  # noqa
from .components import icon  # noqa
from .components import loading  # noqa
from .components import modal  # noqa
from .components import notification  # noqa
from .components import overflow_menu  # noqa
from .components import pagination  # noqa
from .components import progress_indicator  # noqa
from .components import search  # noqa
from .components import shell_header  # noqa
from .components import sidenav  # noqa
from .components import tabs  # noqa
from .components import tag  # noqa
from .components import toggle  # noqa
from .components import tooltip  # noqa
from .components.forms import helpers  # noqa
from .components.forms import search_select  # noqa
from .skeleton import *  # noqa
from .utils import *  # noqa


def render(request, layout, context=None, **response_kwargs):
    if render.CONTEXT_PROCESSORS is None:
        render.CONTEXT_PROCESSORS = tuple(
            import_string(path)
            for path in _builtin_context_processors
            + tuple(
                (settings.TEMPLATES + [{}])[0]
                .get("OPTIONS", {})
                .get("context_processors", [])
            )
        )
    response_kwargs.setdefault("content_type", "text/html")
    defaultcontext = {}
    for processor in render.CONTEXT_PROCESSORS:
        defaultcontext.update(processor(request))
    defaultcontext.update(context or {})
    return HttpResponse(layout.render(defaultcontext), **response_kwargs)


render.CONTEXT_PROCESSORS = None  # type: ignore
