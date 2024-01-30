import fitz
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _


class CustomForm(models.Model):
    title = models.CharField(_("Title"), max_length=255)
    model = models.ForeignKey(
        ContentType, on_delete=models.PROTECT, verbose_name=_("Model")
    )
    pk_fields = models.CharField(
        _("PK fields"),
        max_length=1024,
        blank=True,
        help_text=_(
            """If the form should be used to update items,
this fields specifies the fields that are used to
filter for the instance to update"""
        ),
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _("Custom form")
        verbose_name_plural = _("Custom forms")


class CustomFormField(models.Model):
    customform = models.ForeignKey(
        CustomForm,
        on_delete=models.CASCADE,
        verbose_name=_("Custom form"),
        related_name="customformfields",
        editable=False,
    )
    fieldname = models.CharField(
        _("Field name"),
        max_length=1024,
        help_text=_("See help for list of possible fiel name"),
    )
    label = models.CharField(
        _("Label"),
        max_length=1024,
        help_text=_("Only use to override default label"),
        blank=True,
    )
    help_text = models.TextField(
        _("Help text"),
        help_text=_("Only use to override default help text"),
        blank=True,
    )
    help_text.formfield_kwargs = {"widget": forms.Textarea(attrs={"rows": 1})}

    def __str__(self):
        return self.fieldname

    class Meta:
        verbose_name = _("Custom form field")
        verbose_name_plural = _("Custom form fields")


def pdf_fields(pdffile):
    fields = {}
    pdf = fitz.Document(stream=pdffile)
    for page in pdf:
        widget = page.first_widget
        while widget:
            fields[widget.field_name] = widget.field_value
            widget = widget.next
    pdf.close()
    return fields


class PDFImport(models.Model):
    pdf = models.FileField(_("PDF form"), upload_to="pdf_import")
    customform = models.ForeignKey(CustomForm, on_delete=models.PROTECT)

    @cached_property
    def pdf_fields(self):
        if not self.pdf or not self.pdf.storage.exists(self.pdf.name):
            return {}
        with self.pdf.open() as file:
            return pdf_fields(file.read())

    def save(self, *args, **kwargs):
        generate_fields = self.pk is None
        super().save(*args, **kwargs)
        if generate_fields:
            for i in self.pdf_fields:
                self.fields.create(pdf_field_name=i)

    def __str__(self):
        return _("PDF import for %s") % self.customform

    class Meta:
        verbose_name = _("PDF import")
        verbose_name_plural = _("PDF imports")


class PDFFormField(models.Model):
    pdfimport = models.ForeignKey(
        PDFImport,
        on_delete=models.CASCADE,
        verbose_name=_("PDF form field"),
        related_name="fields",
        editable=False,
    )
    pdf_field_name = models.CharField(_("PDF field name"), max_length=256)
    pdf_field_name.lazy_choices = lambda field, request, instance: [
        (f, f) for f in instance.pdf_fields.keys()
    ]
    customform_field = models.ForeignKey(
        CustomFormField,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        limit_choices_to={"customform": models.F("customform")},
    )
    join = models.CharField(
        _("Join"),
        help_text=_("Join multiple fields with character, use \\n for newline"),
        blank=True,
        max_length=16,
    )
    join.formfield_kwargs = {"strip": False}

    mapping = models.JSONField(
        _("Map value"), help_text=_("Map PDF-field value"), default=dict, blank=True
    )
    mapping.formfield_kwargs = {"widget": forms.Textarea(attrs={"rows": 1})}

    @property
    def fieldname(self):
        return self.customform_field.fieldname if self.customform_field else None

    def __str__(self):
        return self.pdf_field_name

    class Meta:
        verbose_name = _("PDF import field")
        verbose_name_plural = _("PDF import fields")
