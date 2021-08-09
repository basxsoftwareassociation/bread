import json

import htmlgenerator as hg
from django.core import checks
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db import models
from django.urls import reverse
from django.utils.html import mark_safe
from django.utils.translation import gettext_lazy as _
from djangoql.exceptions import DjangoQLError
from djangoql.queryset import apply_search
from djangoql.schema import DjangoQLSchema
from djangoql.serializers import DjangoQLSchemaSerializer

from bread import layout


class QueryValue:
    def __init__(self, queryset, raw):
        self.queryset = queryset
        self.raw = raw

    def __str__(self):
        return self.raw


class QuerySetDescriptor:
    def __init__(self, field):
        self.field = field

    def __get__(self, instance=None, owner=None):
        if instance is None:
            return self
        if self.field.name not in instance.__dict__:
            instance.refresh_from_db(fields=[self.field.name])
        value = instance.__dict__[self.field.name]
        model = getattr(instance, self.field.modelfieldname, None)
        if model and model.model_class():
            return parsequeryexpression(model.model_class().objects, value)
        return QueryValue(None, value)

    def __set__(self, instance, value):
        instance.__dict__[self.field.name] = self.field.get_clean_value(value)


class QuerysetField(models.TextField):
    descriptor_class = QuerySetDescriptor

    def __init__(self, *args, modelfieldname, **kwargs):
        self.modelfieldname = modelfieldname
        kwargs["blank"] = True
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, path, args, {"modelfieldname": self.modelfieldname, **kwargs}

    def contribute_to_class(self, cls, name):
        super().contribute_to_class(cls, name)
        setattr(cls, self.name, self.descriptor_class(self))

    def get_clean_value(self, value):
        return str(value)

    def get_prep_value(self, value):
        super().get_prep_value(self.get_clean_value(value))

    def value_to_string(self, obj):
        return self.get_prep_value(self.value_from_object(obj))

    def get_db_prep_value(self, value, connection, prepared=False):
        return self.get_clean_value(value)

    def formfield(self, **kwargs):
        ret = super().formfield(**kwargs)
        ret.layout = QuerySetFormWidget
        ret.layout_kwargs = {
            "modelfieldname": self.modelfieldname,
            "rows": 1,
            "name": self.name,
        }
        return ret

    def check(self, **kwargs):
        return [
            *super().check(**kwargs),
            *self._check_field_name(),
        ]

    def _check_field_name(self):
        try:
            self.model._meta.get_field(self.modelfieldname)
        except FieldDoesNotExist:
            return [
                checks.Error(
                    "The QuerysetField modelfieldname references the "
                    "nonexistent field '%s'." % self.modelfieldname,
                    obj=self,
                    id="queryfield.E001",
                )
            ]
        else:
            return []

    def validate(self, value, model_instance):
        super().validate(value, model_instance)
        model = getattr(model_instance, self.modelfieldname)
        if not model or not model.model_class():
            raise ValidationError(_("Invalid model '%s' selected") % model)
        parsequeryexpression(
            getattr(model_instance, self.modelfieldname).model_class().objects, value
        )


class QuerySetFormWidget(layout.text_area.TextArea):
    def __init__(self, *args, modelfieldname, name, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        self.boundfield = kwargs.get("boundfield", None)
        self.model = None
        if "boundfield" in kwargs:
            self.model = getattr(
                self.boundfield.form.instance, modelfieldname
            ).model_class()

    def render(self, context):
        if self.model:
            self.append(
                hg.SCRIPT(
                    mark_safe(
                        """
    document.addEventListener("DOMContentLoaded", () => DjangoQL.DOMReady(function () {
    new DjangoQL({
        introspections: %s,
        selector: 'textarea[name=%s]',
        syntaxHelp: '%s',
        autoResize: false
      });
    }));
    """
                        % (
                            json.dumps(
                                DjangoQLSchemaSerializer().serialize(
                                    DjangoQLSchema(self.model)
                                )
                            ),
                            self.name,
                            reverse("reporthelp"),
                        )
                    )
                ),
            )
        return super().render(context)


def parsequeryexpression(basequeryset, expression):
    if not expression:
        return QueryValue(basequeryset.all(), expression)
    try:
        return QueryValue(apply_search(basequeryset, expression), expression)
    except DjangoQLError as e:
        raise ValidationError(str(e))
