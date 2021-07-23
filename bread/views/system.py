import subprocess

import htmlgenerator as hg
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _

from .. import layout
from .util import BreadView


class BreadLoginView(BreadView, LoginView):
    def get_context_data(self, *args, **kwargs):
        return {
            **super().get_context_data(*args, **kwargs),
            "pagetitle": _("Login"),
        }

    def get_layout(self):
        return layout.form.Form.from_fieldnames(
            hg.C("form"), ["username", "password"], submit_label=_("Login")
        )

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["username"].widget.attrs["autofocus"] = True
        return form


class BreadLogoutView(BreadView, LogoutView):
    def get(self, *args, **kwargs):
        super().get(*args, **kwargs)
        return redirect("login")

    def get_context_data(self, *args, **kwargs):
        return {
            **super().get_context_data(*args, **kwargs),
            "pagetitle": _("Logout"),
        }

    def get_layout(self):
        return hg.DIV(_("Logged out"))


def systeminformation(request):
    git_status = ""
    try:
        git_status = subprocess.run(
            ["git", "log", "-n", "5", "--oneline"], capture_output=True, check=True
        ).stdout.decode()
    except subprocess.SubprocessError as e:
        git_status = hg.BaseElement(
            "ERROR",
            hg.BR(),
            str(e),
            hg.BR(),
            getattr(e, "stdout", b"").decode(),
            hg.BR(),
            getattr(e, "stderr", b"").decode(),
        )
    pip_status = ""
    try:
        pip_status = subprocess.run(
            ["pip", "freeze"], capture_output=True, check=True
        ).stdout.decode()
    except subprocess.SubprocessError as e:
        pip_status = hg.BaseElement(
            "ERROR",
            hg.BR(),
            str(e),
            hg.BR(),
            getattr(e, "stdout", b"").decode(),
            hg.BR(),
            getattr(e, "stderr", b"").decode(),
        )

    return render(
        request,
        "bread/base.html",
        context={
            "layout": hg.BaseElement(
                hg.H3("System information"),
                hg.H4("Git log"),
                hg.PRE(hg.CODE(git_status)),
                hg.H4("PIP packages", style="margin-top: 2rem"),
                hg.PRE(hg.CODE(pip_status)),
            ),
            "pagetitle": _("System information"),
        },
    )
