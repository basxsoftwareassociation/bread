from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _


class DocumentTemplate(models.Model):
    name = models.CharField(_("Name"), max_length=255)
    model = models.ForeignKey(
        ContentType,
        on_delete=models.PROTECT,
    )
    file = models.FileField(upload_to="document_templates/")

    def __str__(self):
        return self.name


class Document(models.Model):
    template = models.ForeignKey(
        DocumentTemplate, on_delete=models.CASCADE, related_name="documents"
    )
    file = models.FileField(upload_to="documents/")
