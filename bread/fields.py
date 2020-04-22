from django.db.models.mixin import FieldCacheMixin


class VirtualField(FieldCacheMixin):
    sortable = False
