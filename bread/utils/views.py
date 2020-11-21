import inspect
import itertools

from django.http import HttpResponse
from django.urls import path
from django.views.generic import CreateView
from django.views.generic.edit import SingleObjectMixin
from htmlgenerator import ValueProvider


def generate_path_for_view(view, viewname=None):
    """
    Generates a django path-object from a give view. Class-based views as well as function views are supported:

    Class-based views:
    - The view argument must be a view instance created with ViewClass.as_view()
    - path-arguments should be passed to the as_view call as a dictionary in the form of: {"argname": "argtype"}
    - Views inheriting from SingObjectMixin (except CreateView) will automatically insert an argument of type "int" for the primary key (taken from pk_url_kwarg, slugs are not supported yet)
    Function-based views:
    - The view argument can by any standard django view function.
    - path-arguments will be determined from the the functions parameter-list.
    - Types of path-arguments will be determined from their annotation (>= python3) if available
    """
    viewname = viewname or view.__name__.lower().replace("_", "")
    if hasattr(view, "view_class"):
        pathcomponents = generate_path_for_classview(view, viewname)
    else:
        pathcomponents = generate_path_for_functionview(view, viewname)
    return path("/".join(pathcomponents), view, name=viewname)


def generate_path_for_classview(view, viewname):
    viewpath = [viewname]
    if issubclass(view.view_class, SingleObjectMixin) and not issubclass(
        view.view_class, CreateView
    ):
        viewpath.append(f"<int:{view.view_class.pk_url_kwarg}>")
    if "urlparams" in view.view_initkwargs:
        for param, _type in view.view_initkwargs["urlparams"].items():
            viewpath.append(f"/<{_type}:{param}>")
    return viewpath


def generate_path_for_functionview(view, viewname):
    pathcomponents = [viewname]
    signature = inspect.signature(view)
    for param in itertools.islice(signature.parameters.values(), 1, None):
        pathcomponents.append(
            f"<{param.annotation}:{param.name}>"
            if param.annotation != inspect.Parameter.empty
            else f"<{param.name}>"
        )
    return pathcomponents


class RequestContext(ValueProvider):
    attributename = "request"


def render_layout_to_response(request, layout, context=None):
    return HttpResponse(
        RequestContext(request, layout).render({} if context is None else context)
    )
