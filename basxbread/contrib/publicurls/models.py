from secrets import token_hex
from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.core.signing import TimestampSigner
from django.db import models
from django.urls import Resolver404, resolve, reverse
from django.utils.translation import gettext as _


def validate_url(value):
    try:
        resolve(urlparse(value).path)
    except Resolver404:
        raise ValidationError(
            _("%(value)s is not a valid internal URL"),
            params={"value": value},
        )


class PublicURL(models.Model):
    name = models.CharField(_("Name"), max_length=255)
    url = models.CharField(
        _("URL"),
        max_length=2048,
        validators=[validate_url],
        help_text=_("Internal URL"),
    )
    salt = models.CharField(_("Salt"), max_length=32, editable=False)
    created = models.DateTimeField(_("Created"), auto_now_add=True, editable=False)
    valid_for = models.DurationField(_("Valid for"), null=True, blank=True)
    has_form = models.BooleanField(_("Has form"), default=False)
    thankyou_text = models.TextField(
        _("Thank-you text"),
        default=_("Thank you"),
        help_text=_("Will be shown if a form has successfully been submitted."),
    )

    def publicurl(self):
        return reverse(
            "publicurl",
            kwargs={
                "token": f"{TimestampSigner(salt=self.salt).sign(self.pk)}:{self.salt}"
            },
        )

    setattr(publicurl, "verbose_name", _("Public URL"))

    def absolute_publicurl(self, request):
        return request.build_absolute_uri(location=self.publicurl())

    def save(self, *args, **kwargs):
        if not self.pk:  # prevent to resuse salt when object is copied
            self.salt = None
        if not self.salt:
            self.salt = token_hex(16)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Public URL")
        verbose_name_plural = _("Public URLs")
        ordering = ["-created"]
