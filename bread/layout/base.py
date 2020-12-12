import htmlgenerator as hg
from bread.utils import pretty_fieldname, pretty_modelname
from django.core.exceptions import FieldDoesNotExist


class ModelContext(hg.ValueProvider):
    """Provides a model to marked child elements"""

    attributename = "model"


class ObjectContext(hg.ValueProvider):
    """Provides a model instance to marked child elements """

    attributename = "object"

    def render(self, context):
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
        ret = getattr(self.object, self.fieldname, None)
        ret = ret() if callable(ret) else ret
        yield from self._try_render(ret, context)

    def __repr__(self):
        return f"ModelFieldValue({self.fieldname})"
