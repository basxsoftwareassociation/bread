import htmlgenerator as hg
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _

from .. import layout


class BreadLoginView(LoginView):
    template_name = "bread/base.html"

    def get_context_data(self, *args, **kwargs):
        return {
            **super().get_context_data(*args, **kwargs),
            "layout": layout.form.Form.from_fieldnames(
                hg.C("form"), ["username", "password"], submit_label=_("Login")
            ),
            "pagetitle": _("Login"),
        }

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["username"].widget.attrs["autofocus"] = True
        return form


class BreadLogoutView(LogoutView):
    template_name = "bread/base.html"

    def get(self, *args, **kwargs):
        super().get(*args, **kwargs)
        return redirect("login")

    def get_context_data(self, *args, **kwargs):
        return {
            **super().get_context_data(*args, **kwargs),
            "layout": hg.DIV("Logged out"),
            "pagetitle": _("Logout"),
        }
