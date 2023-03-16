import htmlgenerator as hg
from django import forms
from django.apps import apps
from django.contrib.contenttypes.fields import GenericForeignKey

from .. import layout, utils


def fqn(model):
    return model.__module__ + "." + model.__qualname__


def fieldentry(context):
    field = context["field"]
    ret = hg.BaseElement(hg.SPAN(field.name, style="font-weight: bold"))
    if hasattr(field, "verbose_name"):
        ret.append(" (" + field.verbose_name + ")")
    ret.append(": ")
    typename = hg.BaseElement(fqn(type(field)))
    if field.is_relation:
        if isinstance(field, GenericForeignKey):
            typename.append(f"through ({field.ct_field}, {field.fk_field})")
        else:
            typename.append(" to ")
            typename.append(
                hg.A(
                    fqn(field.target_field.model),
                    href=utils.reverse(
                        "datamodel",
                        query={
                            "app": field.target_field.model._meta.app_label,
                            "highlight": field.target_field.model.__name__,
                        },
                    ),
                )
            )
    ret.append(hg.CODE(typename))
    return ret


def is_same_app_relation(field, currentapp):
    if isinstance(field, GenericForeignKey):
        return False
    if field.is_relation:
        return field.target_field.model._meta.app_label == currentapp
    return False


def modelbox(model, highlighted):
    def fieldlist(context):
        result = []
        for field in hg.resolve_lazy(model, context)._meta.get_fields():
            if getattr(field, "parent_link", False) is False:
                result.append(field)
        return result

    return hg.DIV(
        hg.DIV(
            hg.H5(
                hg.format(
                    "{} {}",
                    hg.F(lambda c: hg.resolve_lazy(model, c).__class__.__name__),
                    hg.SPAN(
                        hg.format("({})", model._meta.verbose_name),
                        style="font-weight: normal",
                    ),
                )
            ),
            style="border-bottom: solid black 1px; padding: 1rem",
        ),
        hg.UL(
            hg.Iterator(
                hg.F(fieldlist),
                "field",
                hg.LI(
                    hg.F(fieldentry),
                    style="padding: 0.25rem",
                ),
            ),
            style="padding: 1rem",
        ),
        style=hg.format(
            "border: solid {}; margin: 1rem;",
            hg.If(
                hg.F(lambda c: c["themodel"].__name__ == highlighted),
                "orange 3px",
                "black 1px",
            ),
        ),
        id=hg.F(lambda c: c["themodel"].__name__),
    )


@utils.aslayout
def datamodel(request):
    appchoices = [
        (app.label, app.verbose_name)
        for app in apps.get_app_configs()
        if len(list(app.get_models())) > 0
    ]

    class Form(forms.Form):
        app = forms.ChoiceField(choices=appchoices)

    form = Form(request.GET)
    models = []
    if form.is_valid():
        for model in apps.get_app_config(form.cleaned_data["app"]).get_models():
            models.append(model)

    return hg.BaseElement(
        hg.H1("Datamodel"),
        hg.DIV(
            layout.forms.Form(
                form,
                layout.forms.FormField("app", onclick="this.closest('form').submit()"),
                method="GET",
            ),
            hg.DIV(
                hg.Iterator(
                    models,
                    "themodel",
                    modelbox(hg.C("themodel"), request.GET.get("highlight")),
                ),
                style="display: flex; flex-wrap: wrap",
            ),
        ),
        hg.SCRIPT(
            hg.mark_safe(
                f"document.getElementById('{request.GET.get('highlight')}').scrollIntoView(scrollIntoViewOptions={{block: 'center'}});"
            )
        ),
    )
