import datetime
import typing

import htmlgenerator as hg
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from basxbread import utils
from basxbread.formatters import is_email_simple
from basxbread.querysetfield import QuerysetField

syntax_email_field = """
Syntax:
- Email: example@example.com
- User/Group: @username
- From object: object.manager.email

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


def validate_direct_attributes(value):
    for v in value.split(","):
        if not v.strip().isidentifier():
            raise ValidationError(
                _("%(v)s is not an allowed field"),
                params={"v": v},
            )


class Action(models.Model):
    description = models.CharField(max_length=255)
    model = models.ForeignKey(
        ContentType,
        verbose_name=_("Model"),
        on_delete=models.PROTECT,
        null=True,  # just for backwards-compatability
    )
    model.formfield_kwargs = {
        "queryset": ContentType.objects.all().order_by("app_label", "model")
    }

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
                extracted_email = hg.resolve_lookup({"object": object}, email) or ""
                if is_email_simple(extracted_email):
                    recipients.append(extracted_email)

        if recipients:
            send_mail(
                subject=utils.jinja_render(self.subject, object=object),
                message=utils.jinja_render(self.message, object=object),
                from_email=None,
                recipient_list=recipients,
            )
        else:
            raise RuntimeError(
                f"No recipients found for {self} (email: '{self.email}')"
            )

    class Meta:
        verbose_name = _("Send email action")
        verbose_name_plural = _("Send email actions")


class Trigger(models.Model):
    description = models.CharField(max_length=255)
    model = models.ForeignKey(
        ContentType,
        verbose_name=_("Model"),
        on_delete=models.PROTECT,
    )
    model.formfield_kwargs = {
        "queryset": ContentType.objects.all().order_by("app_label", "model")
    }
    filter = QuerysetField(_("Filter"), modelfieldname="model")
    enable = models.BooleanField(default=True)
    action = models.ForeignKey(Action, on_delete=models.PROTECT, null=True)
    action.lazy_choices = (
        lambda field, request, instance: Action.objects.all()
        if not instance or not instance.id
        else Action.objects.filter(model=instance.model)
    )

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
    field = models.CharField(
        _("Field"),
        max_length=255,
        blank=True,
        help_text=_(
            "Only trigger when a certain field has changed. Use comma to add multiple fields."
        ),
        validators=[validate_direct_attributes],
    )

    class Meta:
        verbose_name = _("Change trigger")
        verbose_name_plural = _("Change triggers")


INTERVAL_CHOICES = {
    "seconds": (datetime.timedelta(seconds=1), _("Seconds")),
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
        validators=[validate_direct_attributes],
    )
    offset_type = models.CharField(
        _("Offset type"),
        max_length=255,
        choices=tuple((name, value[1]) for name, value in INTERVAL_CHOICES.items()),
        default="days",
    )
    offset_amount = models.IntegerField(
        _("Offset amount"),
        help_text=_("Can be negative (before) or positive (after)"),
        default=0,
    )
    ignore_year = models.BooleanField(
        _("Ignore year"),
        default=False,
        help_text=_("Check this in order to trigger every year"),
    )

    def triggerdates(
        self, object
    ) -> typing.Generator[typing.Optional[datetime.datetime], None, None]:
        for field in (f.strip() for f in self.field.split(",")):
            field_value = getattr(object, field)
            # not sure if doing calls here is a good idea, will see...
            field_value = field_value() if callable(field_value) else field_value
            if field_value is None:
                yield None
                continue
            if isinstance(field_value, datetime.date) and not isinstance(
                field_value, datetime.datetime
            ):
                field_value = timezone.make_aware(
                    datetime.datetime.combine(field_value, datetime.time())
                )
            if self.ignore_year:
                field_value = field_value.replace(year=datetime.date.today().year)

            yield (
                field_value + INTERVAL_CHOICES[self.offset_type][0] * self.offset_amount
            )

    class Meta:
        verbose_name = _("Date trigger")
        verbose_name_plural = _("Date triggers")
