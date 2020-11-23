import inspect
import itertools
import logging
import uuid

from django.contrib.auth.decorators import login_required
from django.urls import path as djangopath

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


def registerurl(view):
    registry.append(view)
    return view


def generate_urlpatterns():
    for view in registry:
        # go through view parameters, except first one which must be "request"
        viewparams = itertools.islice(
            inspect.signature(view).parameters.values(), 1, None
        )
        pathcomponents = [viewbasepath(view)]
        for param in viewparams:
            if param.annotation != inspect.Parameter.empty:
                if param.annotation in PATH_CONVERTERS_MAP:
                    pathcomponents.append(
                        f"<{PATH_CONVERTERS_MAP.get(param.annotation)}:{param.name}>"
                    )
                else:
                    logging.warning(
                        f"view {view}, parameter {param}: {param.annotation} is not available as path converter"
                    )
                    pathcomponents.append(f"<{param.name}>")
            else:
                pathcomponents.append(f"<{param.name}>")

        yield djangopath(
            "/".join(pathcomponents), login_required(view), name=viewname(view)
        )


def viewbasepath(view):
    return view.__module__.lower().replace(".", "/") + "/" + view.__name__.lower()


def viewname(view):
    return view.__module__.lower() + "." + view.__name__.lower()
