from django.db import models
from django.utils.translation import gettext_lazy as _


class DocumentTemplate(models.Model):
    name = models.CharField(_("Name"), max_length=255)
    file = models.FileField(upload_to="document_templates/")

    def __str__(self):
        return self.name
