from django.db import models


class AccessConcreteInstanceMixin:
    """
    Add this mixin to a model class in order to get access to the child instance of
    a multi-table-inheritance model object
    """

    @property
    def concrete(self):
        """Returns the the most concrete instance of the model-instance"""
        for field in self._meta.get_fields():
            if isinstance(field, models.fields.reverse_related.OneToOneRel) and hasattr(
                field, "parent_link"
            ):
                child_object = getattr(self, field.get_accessor_name(), None)
                if child_object:
                    return child_object.concrete
        return self
