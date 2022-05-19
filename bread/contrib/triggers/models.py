import datetime
import typing

import htmlgenerator as hg
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.db import models
from django.template import engines
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from bread.formatters import is_email_simple
from bread.querysetfield import QuerysetField

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
changed, @reminder.date in 2 weeks
"""


class Action(models.Model):
    description = models.CharField(max_length=255)

    def run(self, object):
        raise NotImplementedError()

    def __str__(self):
        return self.description

    class Meta:
        verbose_name = _("Action")
        verbose_name_plural = _("Actions")


class SendEmail(Action):
    email = models.CharField(_("Email"), max_length=255, help_text=syntax_email_field)
    subject = models.CharField(
        _("Subject"),
        max_length=255,
        help_text=_(
            "Will be rendered as a Django template with the name 'object' in the context"
        ),
    )
    message = models.TextField(
        _("Message"),
        help_text=_(
            "Will be rendered as a Django template with the name 'object' in the context"
        ),
    )

    def run(self, object):
        recipients = []
        for email in self.email.split(","):
            email = email.strip()
            if email.startswith("@"):
                user = get_user_model().objects.filter(username=email[1:]).first()
                if user and user.email:
                    recipients.append(user.email)
                else:
                    users = Group.objects.filter(name=email[1:]).first().user_set.all()
                    recipients.extend(u.email for u in users if u.email)
            elif is_email_simple(email):
                recipients.append(email)
            else:  # try to get value from object via accessor
                extracted_email = hg.resolve_lookup(object, email) or ""
                if is_email_simple(extracted_email):
                    recipients.append(extracted_email)
        if recipients:
            send_mail(
                subject=engines["django"]
                .from_string(self.subject)
                .render({"object": object}),
                message=engines["django"]
                .from_string(self.message)
                .render({"object": object}),
                from_email=None,
                recipient_list=recipients,
            )

    class Meta:
        verbose_name = _("Send Email Action")
        verbose_name_plural = _("Send Email Actions")


class Trigger(models.Model):
    description = models.CharField(max_length=255)
    model = models.ForeignKey(
        ContentType,
        verbose_name=_("Model"),
        on_delete=models.PROTECT,
    )
    filter = QuerysetField(_("Filter"), modelfieldname="model")
    enable = models.BooleanField(default=True)
    action = models.ForeignKey(Action, on_delete=models.PROTECT)

    def __str__(self):
        return self.description

    class Meta:
        abstract = True


class DataChangeTrigger(Trigger):
    type = models.TextField(
        _("Type"),
        choices=(
            ("added", _("Added")),
            ("changed", _("Changed")),
            ("deleted", _("Deleted")),
        ),
    )

    class Meta:
        verbose_name = _("Data change trigger")
        verbose_name_plural = _("Data change triggers")


INTERVAL_CHOICES = {
    "minutes": (datetime.timedelta(minutes=1), _("Minutes")),
    "hours": (datetime.timedelta(hours=1), _("Hours")),
    "days": (datetime.timedelta(days=1), _("Days")),
    "weeks": (datetime.timedelta(days=7), _("Weeks")),
    "months": (datetime.timedelta(days=30.5), _("Months")),  # approximation
    "years": (datetime.timedelta(days=365.25), _("Years")),  # approximation
}


class DateFieldTrigger(Trigger):
    field = models.CharField(
        _("Field"),
        max_length=255,
        help_text=_("The field of the selected model which should trigger an action"),
    )
    offset_type = models.CharField(
        _("Offset type"),
        max_length=255,
        choices=tuple((name, value[1]) for name, value in INTERVAL_CHOICES.items()),
    )
    offset_amount = models.IntegerField(
        _("Offset amount"), help_text=_("Can be negative (before) or positive (after)")
    )
    ignore_year = models.BooleanField(
        _("Ignore year"),
        default=False,
        help_text=_("Check this in order to trigger every year"),
    )

    def triggerdate(self, object) -> typing.Optional[datetime.datetime]:
        field_value = getattr(object, self.field)
        if field_value is None:
            return None
        if isinstance(field_value, datetime.date) and not isinstance(
            field_value, datetime.datetime
        ):
            field_value = timezone.make_aware(
                datetime.datetime.combine(field_value, datetime.time())
            )
        if self.ignore_year:
            field_value = field_value.replace(year=datetime.date.today().year)

        return field_value + INTERVAL_CHOICES[self.offset_type][0] * self.offset_amount

    class Meta:
        verbose_name = _("Date field trigger")
        verbose_name_plural = _("Date field triggers")
