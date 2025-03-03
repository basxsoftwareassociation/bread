from typing import List, NamedTuple, Optional, Union

import htmlgenerator as hg
from django.db import models
from django.utils.translation import gettext_lazy as _

from .urls import model_urlname
from .urls import reverse as urlreverse


class LazyHref(hg.Lazy):
    """An element which will resolve lazy. The ``args`` and ``kwargs`` arguments will
    be passed to ``basxbread.utils.urls.reverse``. Every (lazy) item in ``args`` will be
    resolved and every value in ``kwargs`` will be resolved.

    Example usage:

        assert "/settings" == LazyHref(hg.F(lambda c: "settings"))

    """

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def resolve(self, context: dict):
        kwargs = {k: hg.resolve_lazy(v, context) for k, v in self.kwargs.items()}
        # the django reverse function requires url-keyword arguments to be pass
        # in a parameter named "kwarg". This is a bit confusing since kwargs
        # normally referse to the python keyword arguments and not to URL
        # keyword arguments. However, we also want to support lazy URL
        # keywords, so we do the resolving of the actualy URL-kwargs as well
        if "kwargs" in kwargs:
            kwargs["kwargs"] = {
                k: hg.resolve_lazy(v, context) for k, v in kwargs["kwargs"].items()
            }
        if "args" in kwargs:
            kwargs["args"] = [hg.resolve_lazy(arg, context) for arg in kwargs["args"]]
        if "query" in kwargs:
            kwargs["query"] = {
                k: hg.resolve_lazy(v, context) for k, v in kwargs["query"].items()
            }
        return urlreverse(*[hg.resolve_lazy(a, context) for a in self.args], **kwargs)


class ModelHref(LazyHref):
    """
    Works similar to LazyHref but takes a model and a model action
    like "edit", "read", "browse" and generates the URL automatically
    (according to basxbread conventions).
    This is usefull as a replacment of wrapping ``basxbread.utils.urls.reverse_model``
    inside a hg.F element for lazy evalutation of the pk value.

    Example usage:

        assert "/person/browse" == ModelHref(models.Person, "browse").resolve(context)
        assert "/person/edit/1" == ModelHref(
            models.Person, "edit", kwargs={"pk": hg.C("object.pk")}
        ).resolve(context)

    return_to_current: will add a URL query parameter "next=<current_url" to the generated URL

    """

    def __init__(
        self,
        model: Union[models.Model, hg.Lazy],
        name: Union[str, hg.Lazy],
        *args,
        return_to_current: bool = False,
        **kwargs
    ):
        # if this is an instance of a model, we can extract the pk URL argument directly
        # TODO: instance-specific routes which don't use the pk argument will fail

        if isinstance(model, models.Model):
            if "kwargs" not in kwargs:
                kwargs["kwargs"] = {}
            kwargs["kwargs"]["pk"] = model.pk

        if isinstance(model, hg.Lazy):  # assuming "model" is a model instance...
            url = hg.F(
                lambda c: model_urlname(
                    hg.resolve_lazy(model, c), hg.resolve_lazy(name, c)
                )
            )
            # not sure what happens in this case if model is not an instance but a model
            if "kwargs" not in kwargs:
                kwargs["kwargs"] = {}
            kwargs["kwargs"]["pk"] = model.pk
        else:
            url = hg.F(lambda c: model_urlname(model, hg.resolve_lazy(name, c)))
        if return_to_current:
            if "query" not in kwargs:
                kwargs["query"] = {}
            kwargs["query"]["next"] = hg.C("request.get_full_path")

        super().__init__(url, *args, **kwargs)


class Link(NamedTuple):
    href: Union[str, hg.Lazy]
    label: Union[str, hg.Lazy, hg.BaseElement]
    iconname: Optional[str] = "fade"
    permissions: List[str] = []
    attributes: dict = {}
    is_submit: bool = (
        False  # will create a popup and convert the link to an HTTP-post request
    )
    formfields: dict = (
        {}
    )  # allows to specify hidden, prefilled formfields, if is_submit == True
    confirm_text: str = _("Are you sure?")  # only used when is_submit = True

    def has_permission(self, context, obj=None):
        for perm in self.permissions:
            perm = hg.resolve_lazy(perm, context)
            if not context["request"].user.has_perm(perm, obj) and not context[
                "request"
            ].user.has_perm(perm):
                return False
        return True
