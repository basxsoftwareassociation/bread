from django import forms, template

register = template.Library()


@register.filter
def materialize(field):
    if isinstance(
        field.field.widget, (forms.widgets.Select, forms.widgets.SelectMultiple)
    ):
        field.field.widget.attrs["class"] = (
            field.field.widget.attrs.get("class", "") + " no-autoinit"
        )

    return field
