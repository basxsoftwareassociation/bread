from .utils.model_helpers import get_concrete_instance


class AccessConcreteInstanceMixin:
    """
    Add this mixin to a model class in order to get access to the child instance of
    a multi-table-inheritance model object
    """

    @property
    def concrete(self):
        return get_concrete_instance(self)
