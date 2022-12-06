import io
from typing import Union

import htmlgenerator as hg
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import formats
from django.utils.dateformat import DateFormat
from django.utils.timezone import now
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from docxtpl import DocxTemplate
from jinja2.sandbox import SandboxedEnvironment

from basxbread import utils


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
    model.formfield_kwargs = {
        "queryset": ContentType.objects.all().order_by("app_label", "model")
    }
    filename_template = models.TextField(_("Filename template"), blank=True)
    filename_template.formfield_kwargs = {"widget": forms.Textarea(attrs={"rows": 1})}

    def default_context(self):
        return {"now": DateFormat(now())}

    def context(self, object):
        context = {}
        for variable in self.variables.all():
            context[variable.name] = hg.resolve_lookup(object, variable.value)
            if variable.template:
                try:
                    context[variable.name] = utils.jinja_render(
                        variable.template, value=context[variable.name]
                    )
                except Exception as e:
                    context[variable.name] = f"### ERROR: {e} ###"
            else:
                if isinstance(context[variable.name], DateFormat):
                    context[variable.name] = context[variable.name].format(
                        formats.get_format("DATE_FORMAT", lang=get_language())
                    )

        context.update(self.default_context())
        return context

    def render_with(self, object):
        docxtpl_template = DocxTemplate(self.file.path)
        env = SandboxedEnvironment()
        env.filters["map"] = lambda value, map: map.get(value, value)
        docxtpl_template.render(self.context(object), env)

        buf = io.BytesIO()
        docxtpl_template.save(buf)
        buf.seek(0)
        return buf

    def missing_variables(self):
        """Returns (variables_only_in_template, variables_only_in_definition)"""
        intemplate = DocxTemplate(
            self.file.path
        ).get_undeclared_template_variables() - set(self.default_context().keys())
        declared = {v.name for v in self.variables.all()}
        both = intemplate | declared
        return declared ^ both, intemplate ^ both

    def generate_document_url(self, obj: Union[hg.Lazy, models.Model]):
        return utils.ModelHref.from_object(
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
    template = models.TextField(
        _("Template"),
        blank=True,
        help_text=_("Jinja template with 'value' in context"),
    )
    raw_value = models.BooleanField(_("Raw value"), default=False)

    class Meta:
        verbose_name = _("Variable")
        verbose_name_plural = _("Variables")
