import htmlgenerator as hg
from django.conf import settings
from django.http import HttpResponse
from django.template.context import _builtin_context_processors
from django.utils.formats import localize
from django.utils.module_loading import import_string

from bread.utils import pretty_modelname, resolve_modellookup
from bread.utils.urls import reverse_model

from ..formatters import format_value

DEVMODE_KEY = "DEVMODE"


class HasBreadCookieValue(hg.Lazy):
    def __init__(self, cookiename, value, default=None):
        self.cookiename = cookiename
        self.value = value
        self.default = default

    def resolve(self, context):
        if f"bread-{self.cookiename}" in context["request"].session.get(
            "bread-cookies", {}
        ):
            return (
                context["request"].session["bread-cookies"][f"bread-{self.cookiename}"]
                == self.value
            )
        return self.default == self.value


class DevModeOnly(hg.BaseElement):
    def render(self, context):
        if context["request"].session.get(DEVMODE_KEY, False):
            return super().render(context)
        return ""


def fieldlabel(model, accessor):
    label = resolve_modellookup(model, accessor)[-1]
    if hasattr(label, "verbose_name"):
        return label.verbose_name
    if isinstance(label, property):
        return label.fget.__name__.replace("_", " ")
    if callable(label):
        return label.__name__.replace("_", " ")
    return label


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


class ObjectFieldLabel(hg.ContextValue):
    def __init__(self, fieldname, object_contextname="object", title=True):
        """
        :param fieldname: Name of the model field whose value will be rendered
        :param object_contextname: Name of the context object which provides the field value
        """
        super().__init__(object_contextname)
        self.fieldname = fieldname
        self.title = title

    def resolve(self, context):
        ret = fieldlabel(super().resolve(context)._meta.model, self.fieldname)
        return ret.title() if self.title and isinstance(ret, str) else ret


class ObjectFieldValue(hg.ContextValue):
    def __init__(self, fieldname, object_contextname="object", formatter=None):
        """
        :param fieldname: Name of the model field whose value will be rendered
        :param object_contextname: Name of the context object which provides the field value
        :param formatter: function which takes the field value as a single argument and returns a formatted version
        """
        super().__init__(object_contextname)
        self.fieldname = fieldname
        self.formatter = formatter

    def resolve(self, context):
        object = super().resolve(context)
        parts = self.fieldname.split(".")
        # test if the value has a matching get_FIELDNAME_display function
        value = hg.resolve_lookup(
            object, f"{'.'.join(parts[:-1])}.get_{parts[-1]}_display"
        )
        if value is None:
            value = hg.resolve_lookup(object, self.fieldname)
        return (
            self.formatter(value)
            if self.formatter
            else localize(value, use_l10n=settings.USE_L10N)
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
