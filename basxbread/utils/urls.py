import inspect
import itertools
import logging
import uuid
from functools import wraps
from typing import Optional

import htmlgenerator as hg
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.db import models
from django.http import HttpResponse
from django.urls import path as djangopath
from django.urls import reverse_lazy as django_reverse
from django.utils.functional import Promise
from django.utils.http import urlencode
from django.utils.text import format_lazy

from .model_helpers import get_concrete_instance


def reverse(*args, query: Optional[dict] = None, **kwargs):
    """Extended version of the django function ``reverse`` by just adding support
    for an additional parameter ``query`` which can contain query parameters and
    will be encoded automatically.
    """
    if query is not None:
        return format_lazy(
            "{}?{}",
            django_reverse(*args, **kwargs),
            urlencode(
                {k: str(v) if isinstance(v, Promise) else v for k, v in query.items()},
                doseq=True,
            ),
        )
    return django_reverse(*args, **kwargs)


def model_urlname(model, action):
    """Generates a canonical url for a certain action/view on a model"""
    return f"{model._meta.label_lower}.{action}"


def reverse_model(model, action, *args, **kwargs):
    """This works similar to the basxbread function ``reverse`` but simply takes a model
    or an object and an operation name ("browse", "read", "edit", etc) to construct a URL.
    Also, in case the object is part of a django multi-table inheritance, the most-concrete
    object will be used for reversing.
    """
    # make sure we get the most concrete instance in case the model parameter is an object
    if isinstance(model, models.Model):
        model = get_concrete_instance(model)
    return reverse(model_urlname(model, action), *args, **kwargs)


def link_with_urlparameters(request, **kwargs):
    """
    Takes the current URL path and replaces, updates or removes url query
    parameters based on the passed in named arguments, an argument of None or
    empty string will remove the parameter from the URL. Existing parameters in
    the full path which are not one of the named argument will be left
    untouched.
    """
    urlparams = request.GET.copy()
    for parametername, value in kwargs.items():
        urlparams[parametername] = value
        if value in (None, ""):
            del urlparams[parametername]
    return request.path + (f"?{urlparams.urlencode()}" if urlparams else "")


def aslayout(view):
    """Helper function which wraps functions who return a layout to be full django views.
    Non-htmlgenerator.BaseElement responses will simply be passed through."""
    from ..layout.skeleton import default_page_layout

    baselayout = getattr(view, "baselayout", default_page_layout)

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        from .. import layout, menu  # needs to be imported here to avoid cyclic imports

        response = view(request, *args, **kwargs)
        if isinstance(response, hg.BaseElement):
            if settings.AJAX_URLPARAMETER in request.GET:
                return layout.render(request, response)
            return layout.render(
                request,
                baselayout(
                    menu.main,
                    response,
                    hidemenus=settings.HIDEMENUS_URLPARAMETER in request.GET,
                ),
            )
        return response

    return wrapper


def autopath(*args, **kwargs):
    """This function can be used to automatically generate a URL for a view.
    In many situations for internal database applications we are not too conserned
    about the exact name and value of a certain URL but rather a consistent naming
    scheme. So instead of having to write the default django way

        path("myapp/persons/edit/<pk:int>", viewfunction, "edit_person")

    we can just write

        autopath(viewfunction)

    And get a path object with automatically constructed URL-path and URL-name.
    The name of the path (which is e.g. required for calling ``reverse``) can either
    be found in ``./manage.py show_urls`` or be passed directly as argument ``urlname``.

    """
    return generate_path(*args, **kwargs, _DISABLE_WARNING=True)


def generate_path(view, urlname=None, check_function=None, _DISABLE_WARNING=False):
    if not _DISABLE_WARNING:
        import warnings

        warnings.warn(
            "'generate_path' is deprecated, use the compatible function 'autopath' instead",
            UserWarning,
            stacklevel=2,
        )

    check_function = check_function or (lambda user: True)
    pathcomponents = [_viewbasepath(view, urlname)]
    for param, paramtype in _get_view_params(view):
        if paramtype is not None:
            if paramtype in PATH_CONVERTERS_MAP:
                pathcomponents.append(f"<{PATH_CONVERTERS_MAP.get(paramtype)}:{param}>")
            else:
                logging.warning(
                    f"view {view}, parameter {param}: "
                    f"{paramtype} is not available as path converter"
                )
                pathcomponents.append(f"<{param}>")
        else:
            pathcomponents.append(f"<{param}>")

    return djangopath(
        "/".join(pathcomponents),
        user_passes_test(check_function)(view),
        name=urlname or _viewname(view),
    )


def _get_view_params(view):
    if hasattr(view, "view_class"):
        yield from getattr(view.view_class, "urlparams", ()) or ()
    else:
        for param in itertools.islice(
            inspect.signature(view).parameters.values(), 1, None
        ):
            if param.annotation != inspect.Parameter.empty:
                yield param.name, param.annotation
            else:
                yield param.name, None


def _viewbasepath(view, name=None):
    path = (
        (name or _viewname(view))
        .replace(".", "/")
        .replace("basxbread/", "")
        .replace("views/", "")
    )
    if path.endswith("view"):
        path = path[:-4]
    return path


def _viewname(view):
    return f"{view.__module__.lower()}.{view.__name__.lower()}"


def _can_access_media(request, path):
    return request.user.is_staff or path.startswith(
        getattr(settings, "BASXBREAD_PUBLIC_FILES_PREFIX", "static/")
    )


def protectedMedia(request, path):
    """
    Use to protect media files when nginx is serving the files. Usage:

        urlpatterns += [
            path(f"{settings.MEDIA_URL[1:]}<path:path>", protectedMedia, name="media")
        ]

    """
    if _can_access_media(request, path):
        if settings.DEBUG:
            from django.views.static import serve

            return serve(request, path, document_root=settings.MEDIA_ROOT)
        else:
            response = HttpResponse(status=200)
            del response["Content-Type"]
            response["X-Accel-Redirect"] = f"/protected/{path}"
            return response
    else:
        return HttpResponse(status=404)


def default_model_paths(
    model,
    browseview=True,
    readview=True,
    editview=True,
    addview=True,
    deleteview=True,
    copyview=True,
    **kwargs,
):
    """Shortcut to automatically generate a set of urls and views for a model.
    By default the browse-, read-, edit-, add-, delete- and copy-views from basxbread
    are used. These default views can be overriden by passing custom view classes.
    Additional views can be passed via kwargs where as the parameter name is the
    machine-readable name of the view and the value of the parameter is the according
    view class or function.
    """
    from ..views.add import AddView
    from ..views.browse import BrowseView
    from ..views.delete import DeleteView
    from ..views.edit import EditView, generate_copyview
    from ..views.read import ReadView

    defaultview = {
        "browse": BrowseView,
        "read": ReadView,
        "edit": EditView,
        "add": AddView,
        "delete": DeleteView,
    }
    ret = []
    if browseview is not None:
        if browseview is True:
            browseview = defaultview["browse"]
        ret.append(
            autopath(
                browseview.as_view(model=model),
                model_urlname(model, "browse"),
            )
        )
    if readview is not None:
        if readview is True:
            readview = defaultview["read"]
        ret.append(
            autopath(readview.as_view(model=model), model_urlname(model, "read"))
        )
    if editview is not None:
        if editview is True:
            editview = defaultview["edit"]
        ret.append(
            autopath(editview.as_view(model=model), model_urlname(model, "edit"))
        )
    if addview is not None:
        if addview is True:
            addview = defaultview["add"]
        ret.append(autopath(addview.as_view(model=model), model_urlname(model, "add")))
    if deleteview is not None:
        if deleteview is True:
            deleteview = defaultview["delete"]
        ret.append(
            autopath(deleteview.as_view(model=model), model_urlname(model, "delete"))
        )
    if copyview is not None:
        if copyview is True:
            copyview = generate_copyview(model)
        ret.append(autopath(copyview, model_urlname(model, "copy")))

    for viewname, view in kwargs.items():
        if isinstance(view, type):
            ret.append(
                autopath(view.as_view(model=model), model_urlname(model, viewname))
            )
        else:
            ret.append(autopath(view, model_urlname(model, viewname)))

    return ret


# Helpers for the autopath function
class slug:
    pass


class path:
    pass


PATH_CONVERTERS_MAP = {
    str: "str",
    int: "int",
    uuid.UUID: "uuid",
    slug: "slug",
    path: "path",
}
