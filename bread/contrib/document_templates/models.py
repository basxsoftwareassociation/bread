import io
from typing import Union

import htmlgenerator as hg
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _
from docxtpl import DocxTemplate

from bread.utils import ModelHref


class DocumentTemplate(models.Model):
    name = models.CharField(_("Name"), max_length=255)
    file = models.FileField(
        upload_to="document_templates/",
        help_text=_(
            "Must be a *.docx file, use '{{ variable-name }}' to insert variables from below"
        ),
    )

    model = models.ForeignKey(
        ContentType, on_delete=models.PROTECT, verbose_name=_("Model")
    )

    def render_with(self, object):
        docxtpl_template = DocxTemplate(self.file.path)
        docxtpl_template.render(
            {
                variable.name: hg.resolve_lookup(object, variable.value)
                for variable in self.variables.all()
            }
        )

        buf = io.BytesIO()
        docxtpl_template.save(buf)
        buf.seek(0)
        return buf

    def missing_variables(self):
        """Returns (variables_only_in_template, variables_only_in_definition)"""
        intemplate = DocxTemplate(self.file.path).get_undeclared_template_variables()
        declared = {v.name for v in self.variables.all()}
        both = intemplate | declared
        return declared ^ both, intemplate ^ both

    def generate_document_url(self, obj: Union[hg.Lazy, models.Model]):
        return ModelHref.from_object(
            self,
            "generate_document",
            kwargs={"object_pk": obj.pk},
        )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Document Template")
        verbose_name_plural = _("Document Templates")


class DocumentTemplateVariable(models.Model):
    document_template = models.ForeignKey(
        DocumentTemplate, on_delete=models.CASCADE, related_name="variables"
    )
    name = models.CharField(
        _("Name"), max_length=255, help_text=_("Name to use in the template document")
    )
    value = models.CharField(
        _("Value"), max_length=255, help_text=_("Path to the desired value (see help)")
    )
    raw_value = models.BooleanField(_("Raw value"), default=False)

    class Meta:
        verbose_name = _("Variable")
        verbose_name_plural = _("Variables")
