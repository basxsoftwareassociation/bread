from typing import Union

import htmlgenerator as hg
from django.db import models
from django.utils.translation import gettext_lazy as _

from bread.utils import ModelHref


class DocumentTemplate(models.Model):
    name = models.CharField(_("Name"), max_length=255)
    file = models.FileField(upload_to="document_templates/")

    def __str__(self):
        return self.name

    def generate_document_url(self, obj: Union[hg.Lazy, models.Model]):
        return ModelHref(
            self,
            "generate-document",
            kwargs={
                "model_string": obj._meta.label_lower,
                "object_id": obj.pk,
            },
        )
