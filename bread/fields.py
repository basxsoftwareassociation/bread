from django.db.models.fields.mixins import FieldCacheMixin


class VirtualField(FieldCacheMixin):
    sortable = False
