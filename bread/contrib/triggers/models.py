from bread.contrib.reports.fields.queryfield import QuerysetField
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.db import models
from django.utils.translation import gettext_lazy as _

syntax_email_field = """
Syntax:
- Email: example@example.com
- User/Group: @username
- From object: manager.email (actually object.manager.email)

Multiple values van be separated by comma , e.g.
boss@example.com, @adminuser, @reviewteam, primary_email_address.email
"""

syntax_event_field = """
Database change: added, changed, deleted
Date or time in ISO 8601 format: YYYY-MM-DD hh:mm:ss
Date field from object: field:reminder.date 2 weeks ago

Multiple values van be separated by comma , e.g.
changed, YYYY-MM-DD hh:mm:ss, field:reminder.date in 2 weeks
"""


class Action(models.Model):
    description = models.CharField(max_length=255)

    def __str__(self):
        return self.description

    def run(self, object):
        raise NotImplementedError()

    class Meta:
        verbose_name = _("Action")
        verbose_name_plural = _("Actions")


class SendEmail(Action):
    email = models.CharField(_("Email"), max_length=255, help_text=syntax_email_field)
    subject = models.CharField(_("Email"), max_length=255)
    message = models.TextField(_("Message"))

    def run(self, object):
        subject = self.subject
        message = self.message
        recepients = [self.email]
        send_mail(
            subject,
            message,
            from_email=None,
            recipient_list=recepients,
        )

    class Meta:
        verbose_name = _("Send Email")
        verbose_name_plural = _("Send Email Actions")


class Trigger(models.Model):
    model = models.ForeignKey(
        ContentType,
        verbose_name=_("Model"),
        on_delete=models.PROTECT,
    )
    event = models.TextField(_("Event"), help_text=syntax_event_field)
    filter = QuerysetField(_("Filter"), modelfieldname="model")
    enable = models.BooleanField(default=True)
    action = models.ForeignKey(Action, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.model} Trigger: {self.action} on '{self.event}')"

    class Meta:
        verbose_name = _("Trigger")
        verbose_name_plural = _("Triggers")
