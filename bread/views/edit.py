"""
Bread comes with a list of "improved" django views. All views are based
on the standard class-based views of django and are should easily be
extendable and composable by subclassing them. Most of the views require
an argument "admin" which is an instance of the according BreadAdmin class
"""
import urllib

from crispy_forms.layout import Layout
from django import forms
from django.contrib import messages
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.views.generic import CreateView
from django.views.generic import DeleteView as DjangoDeleteView
from django.views.generic import UpdateView
from guardian.mixins import PermissionRequiredMixin

from ..forms.forms import inlinemodelform_factory
from ..utils import get_modelfields


class CustomFormMixin:
    """This mixin takes care of the following things:
    - Allows to pass initial values for form fields via the GET query
    - Converts n-to-many fields into inline forms
    - Set GenericForeignKey fields before saving (not supported by default in django)
    - If "next" is in the GET query redirect to that location on success
    """

    def get_initial(self, *args, **kwargs):
        ret = super().get_initial(*args, **kwargs)
        ret.update(self.request.GET.dict())
        return ret

    def get_form_class(self, form=forms.models.ModelForm):
        return inlinemodelform_factory(
            self.request,
            self.model,
            self.object,
            self.modelfields.values(),
            form,
            self.layout,
        )

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # hide or disable predefined fields passed in GET parameters
        if self.request.method != "POST":
            for field in form.fields:
                if field in self.request.GET:
                    form.fields[field].widget.attrs["readonly"] = True

        # make sure fields appear in original order
        form.order_fields(self.modelfields.keys())
        return form

    def form_valid(self, form):
        with transaction.atomic():
            # set generic foreign key values
            self.object = form.save()
            for name, field in self.modelfields.items():
                if isinstance(field, GenericForeignKey):
                    setattr(self.object, name, form.cleaned_data[name])
            # save inline-objects
            form.save_inline(self.object)
        return super().form_valid(form)


class EditView(
    CustomFormMixin, SuccessMessageMixin, PermissionRequiredMixin, UpdateView
):
    template_name = "bread/custom_form.html"
    admin = None
    accept_global_perms = True

    def get_success_message(self, cleaned_data):
        return f"Saved {self.object}"

    def __init__(self, admin, *args, **kwargs):
        self.admin = admin
        self.model = admin.model
        self.layout = None
        fields = kwargs.get("fields") or self.admin.editfields
        if isinstance(fields, Layout):
            self.layout = fields
            fields = [i[1] for i in fields.get_field_names()]
        self.modelfields = get_modelfields(self.model, fields, for_form=True)
        super().__init__(*args, **kwargs)

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.change_{self.model.__name__.lower()}"]

    def get_success_url(self):
        if "quicksave" in self.request.POST:
            return self.request.get_full_path()
        if self.request.GET.get("next"):
            return urllib.parse.unquote(self.request.GET["next"])
        return self.admin.reverse("index")


class AddView(
    CustomFormMixin, SuccessMessageMixin, PermissionRequiredMixin, CreateView
):
    template_name = "bread/custom_form.html"
    admin = None
    accept_global_perms = True

    def get_success_message(self, cleaned_data):
        return f"Added {self.object}"

    def __init__(self, admin, *args, **kwargs):
        self.admin = admin
        self.model = admin.model
        self.layout = None
        fields = kwargs.get("fields") or self.admin.addfields
        if isinstance(fields, Layout):
            self.layout = fields
            fields = [i[1] for i in fields.get_field_names()]
        self.modelfields = get_modelfields(self.model, fields, for_form=True)
        super().__init__(*args, **kwargs)

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.add_{self.model.__name__.lower()}"]

    def get_permission_object(self):
        return None

    def get_success_url(self):
        if "quicksave" in self.request.POST:
            return self.admin.reverse(
                "edit", pk=self.object.id, query_arguments=self.request.GET
            )
        if self.request.GET.get("next"):
            return urllib.parse.unquote(self.request.GET["next"])
        return self.admin.reverse("index")


class DeleteView(PermissionRequiredMixin, SuccessMessageMixin, DjangoDeleteView):
    template_name = "bread/confirm_delete.html"
    admin = None
    accept_global_perms = True

    def __init__(self, admin, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.admin = admin

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.delete_{self.model.__name__.lower()}"]

    def get_success_url(self):
        messages.info(self.request, f"Deleted {self.object}")
        if self.request.GET.get("next"):
            return urllib.parse.unquote(self.request.GET["next"])
        return self.admin.reverse("index")
