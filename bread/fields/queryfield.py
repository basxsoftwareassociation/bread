import arpeggio
from django.core.exceptions import ValidationError
from django.db import F, Q, models

peg = r"""
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


parser = arpeggio.cleanpeg.ParserPEG(peg, "qexpression")


def parsequeryset(basequeryset, expression):
    # verify the expression is a valid Q-expression
    try:
        parser.parse(expression)
    except arpeggio.NoMatch as e:
        error_string = f"{e}, {e.position}\n{expression}\n{' ' * e.position + '^'}"
        raise ValidationError(
            f"Invalid input for queryset {basequeryset}:\n{error_string}"
        )
    return eval(
        f"qs.filter({expression})",
        globals={},
        locals={"qs": basequeryset, "Q": Q, "F": F},
    )


class QuerySetField(models.Field):
    description = "Queryset for %(model)s"

    def __init__(self, queryset, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queryset = queryset

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, path, self.queryset, args, kwargs

    def get_internal_type(self):
        return "TextField"

    # def from_db_value(self, value, expression, connection):
    # if value is None:
    # return self.queryset.none()
    # return parsequeryset(self.queryset, value)

    def to_python(self, value):
        if isinstance(value, type(self.queryset)):
            return value

        if value is None:
            return self.queryset.none()

        return parsequeryset(self.queryset, value)
