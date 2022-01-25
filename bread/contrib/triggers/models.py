import datetime

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

    def __str__(self):
        return self.description

    def run(self, object):
        raise NotImplementedError()

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
        recepients = []
        for email in self.email.split(","):
            email = email.strip()
            if email.startswith("@"):
                user = get_user_model().objects.filter(username=email[1:]).first()
                if user and user.email:
                    recepients.append(user.email)
                else:
                    users = Group.objects.filter(name=email[1:]).first().user_set.all()
                    recepients.extend(u.email for u in users if u.email)
            elif is_email_simple(email):
                recepients.append(email)
            else:  # try to get value from object via accessor
                extracted_email = hg.resolve_lookup(object, email) or ""
                if is_email_simple(extracted_email):
                    recepients.append(extracted_email)
        if recepients:
            send_mail(
                subject=engines["django"]
                .from_string(self.subject)
                .render({"object": object}),
                message=engines["django"]
                .from_string(self.message)
                .render({"object": object}),
                from_email=None,
                recipient_list=recepients,
            )

    class Meta:
        verbose_name = _("Send Email Action")
        verbose_name_plural = _("Send Email Actions")


class Trigger(models.Model):
    model = models.ForeignKey(
        ContentType,
        verbose_name=_("Model"),
        on_delete=models.PROTECT,
    )
    filter = QuerysetField(_("Filter"), modelfieldname="model")
    enable = models.BooleanField(default=True)
    action = models.ForeignKey(Action, on_delete=models.PROTECT)

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

    def __str__(self):
        return f"{self.model} Trigger: {self.action} when {self.type})"

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
    field = models.CharField(max_length=255)
    offset_type = models.CharField(
        max_length=255,
        choices=tuple((name, value[1]) for name, value in INTERVAL_CHOICES.items()),
    )
    offset_amount = models.IntegerField(
        help_text=_("Can be negative (before) or positive (after)")
    )

    def triggerdate(self, object):
        field_value = getattr(object, self.field)
        if field_value is None:
            return None
        if isinstance(field_value, datetime.date) and not isinstance(
            field_value, datetime.datetime
        ):
            field_value = timezone.make_aware(
                datetime.datetime.combine(field_value, datetime.time())
            )

        return field_value + INTERVAL_CHOICES[self.offset_type][0] * self.offset_amount

    def __str__(self):
        return f"{self.model} Trigger: {self.action} on: {abs(self.offset_amount)} {self.get_offset_type_display()} {'before' if self.offset_amount < 0 else 'after'} {self.model}.{self.field})"

    class Meta:
        verbose_name = _("Date field trigger")
        verbose_name_plural = _("Date field triggers")