from typing import NamedTuple, Union

import htmlgenerator as hg

from .urls import model_urlname
from .urls import reverse as urlreverse


class LazyHref(hg.Lazy):
    """An element which will resolve lazy. The ``args`` and ``kwargs`` arguments will
    be passed to ``bread.utils.urls.reverse``. Every item in ``args`` will be resolved
    and every value in ``kwargs`` will be resolved.

    Example usage:

        assert "/settings" == LazyHref(hg.F(lambda c: "settings"))

    """

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def resolve(self, context: dict):
        return urlreverse(
            *[hg.resolve_lazy(a, context) for a in self.args],
            **{k: hg.resolve_lazy(v, context) for k, v in self.kwargs.items()}
        )


class ModelHref(LazyHref):
    """
    Works similar to LazyHref but takes a model and a model action
    like "edit", "read", "browse" and generates the URL automatically
    (according to bread conventions).
    This is usefull as a replacment of wrapping ``bread.utils.urls.reverse_model``
    inside a hg.F element for lazy evalutation of the pk value.

    Example usage:

        assert "/person/browse" == ModelHref(models.Person, "browse")
        assert "/person/edit/1" == ModelHref(models.Person, "edit", kwargs={"pk": F("object.pk")})

    """

    def __init__(self, model, name, *args, **kwargs):
        super().__init__(model_urlname(model, name), *args, **kwargs)


def try_call(var, *args, **kwargs):
    return var(*args, **kwargs) if callable(var) else var


class Link(NamedTuple):
    href: Union[str, LazyHref]
    label: str
    iconname: str = "fade"
    permissions: list[str] = []

    def has_permission(self, request, obj=None):
        return all(
            [
                request.user.has_perm(perm, obj) or request.user.has_perm(perm)
                for perm in self.permissions
            ]
        )
