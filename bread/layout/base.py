import htmlgenerator as hg
from django.core.exceptions import FieldDoesNotExist
from django.utils import formats

from bread.utils import get_concrete_instance, pretty_fieldname, pretty_modelname
from bread.utils.urls import reverse_model


class RequestContext(hg.ValueProvider):
    """Provides the request to marked child elements"""

    attributename = "request"


class ModelContext(hg.ValueProvider):
    """Provides a model to marked child elements"""

    attributename = "model"


class ObjectContext(hg.ValueProvider):
    """Provides a model instance to marked child elements """

    attributename = "object"

    def render(self, context):
        self.value = get_concrete_instance(hg.resolve_lazy(self.value, context, self))
        return super().render(context)


class ModelFieldLabel(ModelContext.Binding(), ObjectContext.Binding()):
    def __init__(self, fieldname):
        self.fieldname = fieldname

    def render(self, context):
        if not hasattr(self, "model") and hasattr(self, "object"):
            self.model = self.object
        try:
            yield pretty_fieldname(self.model._meta.get_field(self.fieldname))
        except FieldDoesNotExist:
            yield from self._try_render(
                getattr(getattr(self.model, self.fieldname, None), "verbose_name", ""),
                context,
            )

    def __repr__(self):
        return f"ModelFieldLabel({self.fieldname})"


class ModelName(ModelContext.Binding(), ObjectContext.Binding()):
    def __init__(self, plural=False):
        self.plural = plural

    def render(self, context):
        if not hasattr(self, "model") and hasattr(self, "object"):
            self.model = self.object
        yield str(pretty_modelname(self.model, self.plural))

    def __repr__(self):
        return "ModelName()"


class ModelFieldValue(ObjectContext.Binding()):
    def __init__(self, fieldname):
        self.fieldname = fieldname

    def render(self, context):
        object = self.object
        for accessor in self.fieldname.split("."):
            object = getattr(object, accessor, None)
            object = object() if callable(object) else object
        yield from self._try_render(formats.localize(object), context)

    def __repr__(self):
        return f"ModelFieldValue({self.fieldname})"


class ObjectAction(ObjectContext.Binding()):
    def __init__(self, action, *args, **kwargs):
        self.action = action
        self.args = args
        self.kwargs = kwargs

    def render(self, context):
        yield str(
            reverse_model(
                self.object,
                self.action,
                args=self.args,
                kwargs={
                    **self.kwargs,
                    "pk": self.object.pk,
                },
            )
        )

    def __repr__(self):
        return f"ModelAction({self.action}, {self.args}, {self.kwargs})"


class ObjectLabel(ObjectContext.Binding()):
    def render(self, context):
        yield str(self.object)


# TODO: this element might be totaly unusable since valueproviders will not propagate values down
# either remove this or move it to htmlgenerator and load and walk the layout inside the valueproviders, somehow...
class Include(hg.BaseElement):
    """Element which will render a layout registered in the layout registry"""

    def __init__(self, templatename):
        super().__init__(self)
        self.templatename = templatename

    def render(self, request, context):
        from .registry import (
            get_layout,
        )  # late import necessary to make sure all layouts are registered

        return get_layout(self.templatename)().render(request, context)

    def __repr__(self):
        from .registry import (
            get_layout,
        )  # late import necessary to make sure all layouts are registered

        return get_layout(self.templatename).__repr__()


def aslink_attributes(href):
    """
    Shortcut to generate HTMLElement attributes to make any element behave like a link.
    This should normally be used like this: hg.DIV("hello", **aslink_attributes('google.com'))
    """
    return {
        "onclick": hg.BaseElement("document.location = '", href, "'"),
        "onauxclick": hg.BaseElement("window.open('", href, "', '_blank')"),
        "style": "cursor: pointer",
    }
