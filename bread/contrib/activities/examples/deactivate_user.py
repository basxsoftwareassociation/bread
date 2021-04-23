from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import models

from . import base


class UserExists(base.DecisionBase):
    def decide(self, activity):
        return activity.user is not None


class SetUserInactive(base.ActionBase):
    def is_done(self, activity):
        if self.activity.user.is_active:
            self.activity.user.is_active = False
            self.activity.user.save()
        return True


class NotifyUser(base.ActionBase):
    def __init__(self, get_user_func, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.get_user_func = get_user_func

    def is_done(self, activity):
        user = self.get_user_func(activity)
        send_mail(
            "Account disabled",
            f"The account of user {activity.user} has been disabled.",
            None,
            [user.email],
            fail_silently=False,
        )
        return True


class DeactivateUser(base.ActivityBase):
    confirmed = models.BooleanField(default=False)

    start = base.Initial()
    userexists = UserExists()
    setUserInactive = SetUserInactive()
    fork = base.Fork()
    email_user = NotifyUser(lambda a: a.user)
    email_admin = NotifyUser(lambda a: User.objects.filter(is_superuser=True).first())
    join = base.Join()
    merge = base.Merge()
    end = base.ActivityFinal()

    DIAGRAM = {
        start: userexists,
        userexists: (setUserInactive, merge),
        setUserInactive: fork,
        fork: (email_user, email_admin),
        email_user: join,
        email_admin: join,
        join: merge,
        merge: end,
    }
