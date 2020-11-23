import htmlgenerator
from bread.utils import pretty_fieldname, pretty_modelname


def html_id(object):
    """Generate a unique HTML id from an object"""
    # not sure how bad this one is regarding possible security issues,
    # it might leak memory layout to the frontend, at least in the CPython implementation
    # but I think it is sufficient safe
    # reasoning:
    # - id: We want a guaranteed unique ID. Since the lifespan of an HTML-response is shorted than that of the working process, this should be fine. Python might re-use objects and their according memory, but it seems unlikely that this will be an issue.
    # - str: passing an int (from id) into the hash-function will result in the int beeing passed back. We need to convert the id to a string in order have hash doing some real hashing
    # - hash: Prevent the leaking of any memory layout information. hash is of course not secure but should not be trivial to reverse.
    # - str: Because html-ids are strings we convert again to string
    # - [1:]: in case there is a leading "-" we remove the first character
    return str(hash(str(id(object))))[1:]


class ModelContext(htmlgenerator.ValueProvider):
    """Provides a model to marked child elements"""

    attributename = "model"

    def __init__(self, model, *children):
        super().__init__(model, *children)


class ObjectContext(htmlgenerator.ValueProvider):
    """Provides a model instance to marked child elements """

    attributename = "object"

    def __init__(self, object, *children):
        super().__init__(object, *children)


class ModelFieldLabel(ModelContext.Binding(), ObjectContext.Binding()):
    def __init__(self, fieldname):
        self.fieldname = fieldname

    def render(self, context):
        if not hasattr(self, "model") and hasattr(self, "object"):
            self.model = self.object
        yield pretty_fieldname(self.model._meta.get_field(self.fieldname))

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
        yield from self._try_render(getattr(self.object, self.fieldname, None), context)

    def __repr__(self):
        return f"ModelFieldValue({self.fieldname})"
