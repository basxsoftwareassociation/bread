from django.contrib.auth.views import LoginView, LogoutView
from django.utils.translation import gettext_lazy as _

from .. import layout


class BreadLoginView(LoginView):
    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["username"].widget.attrs["autofocus"] = True
        self.layout = lambda request: layout.form.Form.from_fieldnames(
            form, ["username", "password"], submit_label=_("Login")
        )
        return form


class BreadLogoutView(LogoutView):
    pass
