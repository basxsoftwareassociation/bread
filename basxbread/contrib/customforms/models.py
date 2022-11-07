from django import forms
from django.contrib.contenttypes.models import ContentType
from django.db import models
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
