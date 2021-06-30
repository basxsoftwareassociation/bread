import inspect
import itertools
import logging
import uuid
from functools import wraps

from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.db import models
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import path as djangopath
from django.urls import reverse_lazy as django_reverse
from django.utils.http import urlencode
from django.utils.text import format_lazy

from .model_helpers import get_concrete_instance


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


def model_urlname(model, action):
    """Generates a canonical url for a certain action/view on a model"""
    return f"{model._meta.label_lower}.{action}"


def reverse(*args, **kwargs):
    query = kwargs.pop("query", {})
    if query:
        return format_lazy(
            "{}?{}",
            django_reverse(*args, **kwargs),
            urlencode(query),
        )
    return django_reverse(*args, **kwargs)


def link_with_urlparameters(request, **kwargs):
    """Takes the current URL path and replaces, updates or removes url query parameters based on the passed in named arguments, an argument of None or empty string will remove the parameter from the URL. Existing parameters in the full path which are not one of the named argument will be left untouched."""
    urlparams = request.GET.copy()
    for parametername, value in kwargs.items():
        urlparams[parametername] = value
        if value in (None, ""):
            del urlparams[parametername]
    return request.path + (f"?{urlparams.urlencode()}" if urlparams else "")


def reverse_model(model, action, *args, **kwargs):
    # make sure we get the most concrete instance in case the model parameter is an object
    if isinstance(model, models.Model):
        model = get_concrete_instance(model)
    return reverse(model_urlname(model, action), *args, **kwargs)


def aslayout(view):
    """Helper function to let views return an element tree from htmlgenerator"""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        return render(
            request, "bread/base.html", {"layout": view(request, *args, **kwargs)}
        )

    return wrapper


def generate_path(view, urlname=None, check_function=None):
    def default_check(user):
        return user.is_authenticated and user.is_active

    check_function = check_function or default_check
    pathcomponents = [viewbasepath(view, urlname)]
    for param, paramtype in get_view_params(view):
        if paramtype is not None:
            if paramtype in PATH_CONVERTERS_MAP:
                pathcomponents.append(f"<{PATH_CONVERTERS_MAP.get(paramtype)}:{param}>")
            else:
                logging.warning(
                    f"view {view}, parameter {param}: {paramtype} is not available as path converter"
                )
                pathcomponents.append(f"<{param}>")
        else:
            pathcomponents.append(f"<{param}>")

    return djangopath(
        "/".join(pathcomponents),
        user_passes_test(check_function)(view),
        name=urlname or viewname(view),
    )


def get_view_params(view):
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


def viewbasepath(view, name=None):
    path = (
        (name or viewname(view))
        .replace(".", "/")
        .replace("bread/", "")
        .replace("views/", "")
    )
    if path.endswith("view"):
        path = path[:-4]
    return path


def viewname(view):
    return f"{view.__module__.lower()}.{view.__name__.lower()}"


def can_access_media(request, path):
    return request.user.is_staff or path.startswith(settings.BREAD_PUBLIC_FILES_PREFIX)


def protectedMedia(request, path):
    """
    Protect media files
    """
    if can_access_media(request, path):
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
):
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
            generate_path(
                browseview.as_view(model=model, bulkactions=browseview.bulkactions),
                model_urlname(model, "browse"),
            )
        )
    if readview is not None:
        if readview is True:
            readview = defaultview["read"]
        ret.append(
            generate_path(readview.as_view(model=model), model_urlname(model, "read"))
        )
    if editview is not None:
        if editview is True:
            editview = defaultview["edit"]
        ret.append(
            generate_path(editview.as_view(model=model), model_urlname(model, "edit"))
        )
    if addview is not None:
        if addview is True:
            addview = defaultview["add"]
        ret.append(
            generate_path(addview.as_view(model=model), model_urlname(model, "add"))
        )
    if deleteview is not None:
        if deleteview is True:
            deleteview = defaultview["delete"]
        ret.append(
            generate_path(
                deleteview.as_view(model=model), model_urlname(model, "delete")
            )
        )
    if copyview is not None:
        if copyview is True:
            copyview = generate_copyview(model)
        ret.append(generate_path(copyview, model_urlname(model, "copy")))

    return ret
