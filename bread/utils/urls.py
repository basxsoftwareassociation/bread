import inspect
import itertools
import logging
import uuid
from functools import wraps

from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import path as djangopath
from django.urls import reverse_lazy as django_reverse
from django.utils.http import urlencode
from django.utils.text import format_lazy
from django.views import View

registry = []


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


def reverse_model(model, action, *args, **kwargs):
    return reverse(model_urlname(model, action), *args, **kwargs)


def registermodelurl(model, name, view, check_function=None, **view_kwargs):
    check_function = check_function or (
        lambda user: user.has_perm(
            f"{model._meta.app_label}.view_{model._meta.model_name}"
        )
    )

    if isinstance(view, type) and issubclass(view, View):
        view = view.as_view(model=model, **view_kwargs)
    registerurl(model_urlname(model, name), check_function)(view)


# decorators
def registerurl(
    urlname=None, check_function=lambda user: user.is_authenticated and user.is_active
):
    if callable(urlname):
        registry.append((urlname, None, check_function))
        return urlname

    """register a view in order to generate URLs automatically
    check is a function which takes a user object as single parameter and returns true if the user is allowed to access the view"""

    def registerurl_wrapper(view):
        registry.append((view, urlname, check_function))
        return view

    return registerurl_wrapper


# TODO: test this function
def unregisterurl(name):
    remove = []
    for i, view_config in enumerate(registry):
        if name in (view_config[0], view_config[1], viewname(view_config[0])):
            remove += i
    for i in remove:
        del registry[i]


def aslayout(view):
    """Helper function to let views return an element tree from htmlgenerator"""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        return render(
            request, "bread/layout.html", {"layout": view(request, *args, **kwargs)}
        )

    return wrapper


def generate_urlpatterns():
    for view, urlname, check_function in registry:
        pathcomponents = [viewbasepath(view, urlname)]
        for param, paramtype in get_view_params(view):
            if paramtype is not None:
                if paramtype in PATH_CONVERTERS_MAP:
                    pathcomponents.append(
                        f"<{PATH_CONVERTERS_MAP.get(paramtype)}:{param}>"
                    )
                else:
                    logging.warning(
                        f"view {view}, parameter {param}: {paramtype} is not available as path converter"
                    )
                    pathcomponents.append(f"<{param}>")
            else:
                pathcomponents.append(f"<{param}>")

        yield djangopath(
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
