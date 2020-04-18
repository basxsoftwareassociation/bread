from django.db import models


class VirtualField(models.fields.Field):
    sortable = False
