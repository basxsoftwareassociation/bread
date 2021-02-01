"""
The Bread frameworks provides a view util views to provide special functionality.
"""

from django.contrib.auth.views import LoginView, LogoutView

from .. import layout as layout


class BreadLoginView(LoginView):
    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["username"].widget.attrs["autofocus"] = True
        self.layout = lambda request: layout.form.Form.from_fieldnames(
            form, ["username", "password"]
        )
        return form


class BreadLogoutView(LogoutView):
    pass
