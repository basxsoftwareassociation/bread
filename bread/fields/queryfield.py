import arpeggio
import arpeggio.cleanpeg
from django import forms
from django.apps import apps
from django.core.exceptions import FieldError, ValidationError
from django.db import models
from django.utils.functional import cached_property

# this is a PEG to verify that a string can be passed to eval() and return a
# valid result which can be passe to for Queryset.filter
# the toplevel expression is, similar to django, just a shortcut in case no
# Q-operators are necessary
peg = r"""
    toplevel_expression = paramlist / qexpression
    qexpression  = ( qobj / nestedqexpression / notqexpression ) (binaryqoperator qexpression)* EOF
    nestedqexpression = "(" qexpression ")"
    notqexpression = "~" qexpression
    binaryqoperator = "&" / "|"
    qobj = "Q(" paramlist ")"
    paramlist = param (", " param)*
    param = fieldlookup "=" expression
    fieldlookup = r"[a-zA-Z_]\w*"
    expression = ( literal / nestedExpression / unaryExpression ) (binaryOperator expression)*
    nestedExpression = "(" expression ")"
    unaryExpression = unaryOperator expression
    unaryOperator = "+" / "-"
    binaryOperator = "+" / "-" / "*" / "/" / "%" / "**" / "//"
    literal = stringliteral / numberliteral / fliteral
    stringliteral = r'"[^"]*"' / r"'[^']*'"
    numberliteral = r"[0-9]+(\.[0-9]*)?"
    fliteral = 'F(' stringliteral ')'
    """


parser = arpeggio.cleanpeg.ParserPEG(peg, "toplevel_expression")


def checkexpression(expression):
    try:
        parser.parse(expression)
    except arpeggio.NoMatch as e:
        raise ValidationError(
            f'"{expression}" cannot be parsed as filter expression: {e}'
        )


def parsequeryexpression(basequeryset, expression):
    if not isinstance(expression, str):
        raise RuntimeError(
            f"expression '{expression}' needs to be of type str instead of {type(expression)}"
        )
    if not expression:
        return basequeryset
    checkexpression(expression)
    try:
        query = eval(  # nosec for now, will later be replaced with DjangoQL
            f"qs.filter({expression})",
            {},
            {"qs": basequeryset, "Q": models.Q, "F": models.F},
        )
    except FieldError as e:
        raise ValidationError(str(e))
    return Query(query, expression)


class QuerySetFormWidget(forms.Textarea):
    def format_value(self, value):
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        return value.raw


class Query:
    def __init__(self, queryset, raw):
        self.queryset = queryset
        self.raw = raw


class QuerySetField(models.TextField):
    def __init__(self, modelname, *args, **kwargs):
        self.modelname = modelname
        if hasattr(self.modelname, "_meta"):
            self.modelname = self.modelname._meta.label
        super().__init__(*args, **kwargs)

    @cached_property
    def querymodel(self):
        return apps.get_model(self.modelname)

    @cached_property
    def queryset(self):
        return self.querymodel.objects.get_queryset()

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, path, [self.modelname] + args, kwargs

    def from_db_value(self, value, expression, connection):
        if value is None:
            return Query(self.queryset.none(), "")
        return parsequeryexpression(self.queryset, value)

    def to_python(self, value):
        if isinstance(value, Query):
            return value

        if value is None:
            return Query(self.queryset.none(), "")

        return parsequeryexpression(self.queryset, value)

    def get_prep_value(self, value):
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        return value.raw

    def formfield(self, **kwargs):
        kwargs["widget"] = QuerySetFormWidget
        return super().formfield(**kwargs)

    def validate(self, value, model_instance):
        super().validate(value, model_instance)
        if isinstance(value, Query):
            return
        parsequeryexpression(self.queryset, value)
