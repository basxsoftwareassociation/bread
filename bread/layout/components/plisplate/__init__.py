from bread.utils import pretty_fieldname

import plisplate
from plisplate import *  # noqa

from . import button, datatable, form, grid, icon, notification  # noqa


class Model(plisplate.ValueProvider):
    """Provides a model to marked child elements"""

    attributename = "model"

    def __init__(self, model, *children):
        super().__init__(model, "model", *children)


class Object(plisplate.ValueProvider):
    """Provides a model instance to marked child elements """

    attributename = "object"

    def __init__(self, object, *children):
        super().__init__(object, *children)


class ModelFieldLabel(Model.ConsumerMixin(), Object.ConsumerMixin()):
    def __init__(self, fieldname):
        self.fieldname = fieldname

    def render(self, context):
        yield pretty_fieldname(
            getattr(self, "model", getattr(self, "object", None))._meta.get_field(
                self.fieldname
            )
        )

    def __repr__(self):
        return f"FieldLabel({self.fieldname})"


class ModelFieldValue(Object.ConsumerMixin()):
    def __init__(self, fieldname):
        self.fieldname = fieldname

    def render(self, context):
        yield from self._try_render(getattr(self.object, self.fieldname, None), context)
