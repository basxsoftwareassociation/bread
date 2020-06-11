from django.db import models


class AccessChildMixin:
    """
    Add this mixin to a model class in order to get access to the child instance of
    multi-table-inheritance object
    """

    def get_child(self):
        """Returns the child instance of this instance if existing, else None"""
        for field in self._meta.get_fields():
            if isinstance(field, models.fields.reverse_related.OneToOneRel) and hasattr(
                field, "parent_link"
            ):
                child_object = getattr(self, field.get_accessor_name(), None)
                if child_object:
                    return child_object
        return None
