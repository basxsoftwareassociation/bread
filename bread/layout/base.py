import htmlgenerator as hg
from django.conf import settings
from django.http import HttpResponse
from django.template.context import _builtin_context_processors
from django.utils.module_loading import import_string

from bread.utils import pretty_modelname, resolve_modellookup
from bread.utils.urls import reverse_model

from ..formatters import format_value


class HasBreadCookieValue(hg.Lazy):
    def __init__(self, cookiename, value, default=None):
        self.cookiename = cookiename
        self.value = value
        self.default = default

    def resolve(self, context):
        if f"bread-{self.cookiename}" in context["request"].session["bread-cookies"]:
            return (
                context["request"].session["bread-cookies"][f"bread-{self.cookiename}"]
                == self.value
            )
        return self.default == self.value


def fieldlabel(model, accessor):
    label = resolve_modellookup(model, accessor)[-1]
    if isinstance(label, property):
        return getattr(label, "verbose_name", None) or label.fget.__name__
    return getattr(label, "verbose_name", None) or label


def objectaction(object, action, *args, **kwargs):
    kwargs["kwargs"] = {"pk": object.pk}
    return str(
        reverse_model(
            object,
            action,
            *args,
            **kwargs,
        )
    )


def aslink_attributes(href):
    """
    Shortcut to generate HTMLElement attributes to make any element behave like a link.
    This should normally be used like this: hg.DIV("hello", \\*\\*aslink_attributes('google.com'))
    """
    return {
        "onclick": hg.BaseElement("document.location = '", href, "'"),
        "onauxclick": hg.BaseElement("window.open('", href, "', '_blank')"),
        "style": "cursor: pointer",
    }


class ModelName(hg.ContextValue):
    def resolve(self, context):
        return pretty_modelname(super().resolve(context))


class FormattedContextValue(hg.ContextValue):
    def resolve(self, context):
        return str(format_value(super().resolve(context)))


class ObjectFieldLabel(hg.Lazy):
    def __init__(self, fieldname):
        self.fieldname = fieldname

    def resolve(self, context):
        return fieldlabel(context["object"]._meta.model, self.fieldname)


# TODO compare with formatters.format_value and refactor according to discussion:
# https://github.com/basxsoftwareassociation/bread/pull/66/files#r684120073
class ObjectFieldValue(hg.Lazy):
    def __init__(self, fieldname):
        self.fieldname = fieldname

    def resolve(self, context):
        return (
            getattr(context["object"], f"get_{self.fieldname}_display")()
            if hasattr(context["object"], f"get_{self.fieldname}_display")
            else getattr(context["object"], self.fieldname)
        )


FC = FormattedContextValue


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


render.CONTEXT_PROCESSORS = None
