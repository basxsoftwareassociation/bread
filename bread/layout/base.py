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


# notes on changes (this may be removed py wipascal):
# By inheriting from ContextValue we can use the parameter
# "object_contextname" to query any object from the context which
# is "dot-accessible". E.g we could use ObjectFieldValue("primary_email_address", "row")
# or ObjectFieldValue("email", "row.primary_email_address")
# in the second example we "extract the email-address object from the context and
# use the field "email" of that object.
#
# The object can then be obtained from the context by calling super().resolve(context)


class ObjectFieldLabel(hg.ContextValue):
    def __init__(self, fieldname, object_contextname="object"):
        super().__init__(object_contextname)
        self.fieldname = fieldname

    def resolve(self, context):
        return fieldlabel(super().resolve(context)._meta.model, self.fieldname)


# notes on changes (this may be removed py wipascal):
# The additional complexity comes from a use case where
# we want to display a value which spans one or multiple relationships
# E.g. if we have a table of persons and the object context-name is
# "row" and we want to display the country, we would want to specifiy the field
# as "primary_postal_address.country". This is what is already mentioned in the
# first note above, but we make use of hg.resolve_lookup instead of fieldlabel (
# because resolve_lookup is much more generic, while fieldlabel only works with
# django models and has therefore a bit more information when doing the lookup).

# If "primary_postal_address.country" would have a "get_country_display" method,
# then we want to call that method as "primary_postal_address.get_country_display".
# this is why we do the slightly ugly string-splitting

# Note that we might also want to access a non-django-field value like
# "primary_postal_address.country.name" which works with the implementation below

# I think it is good if we have a standard way to display database values and field
# labels, so I am all for replacing the existing methods with a consistent one.
# The amount of "magic" or "genericnes" that I would like to have here is because
# it makes prototyping much faster. The dot-lookup-anything idea comes from
# traditional html-template systems like the django template language, hg.resolve_lookup
# is copied and adjust from the django template system.


class ObjectFieldValue(hg.ContextValue):
    def __init__(self, fieldname, object_contextname="object", formatter=None):
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
        return self.formatter(value) if self.formatter else value


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
