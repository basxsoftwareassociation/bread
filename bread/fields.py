from django.db.models import Field
from django.db.models.fields.mixins import FieldCacheMixin


class VirtualField(Field, FieldCacheMixin):
    sortable = False
