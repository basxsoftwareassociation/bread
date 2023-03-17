import htmlgenerator as hg
from django import forms
from django.apps import apps
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.translation import gettext_lazy as _

from .. import layout, utils


def fqn(model):
    result = model.__module__.split(".", 1)[0] + "." + model.__qualname__
    if result.startswith("django."):
        return model.__qualname__
    return result


def fieldentry(context):
    field = context["field"]
    label = hg.DIV(
        hg.SPAN(
            " + ",
            style="font-size: 1.2rem; cursor: pointer; user-select: none;",
            onclick="infoblock = this.parentElement.nextElementSibling;"
            "infoblock.style.display = infoblock.style.display == 'block' ? 'none' : 'block'",
        ),
        hg.SPAN(field.name, style="font-weight: bold"),
    )
    if hasattr(field, "verbose_name"):
        label.append(" (" + field.verbose_name + ")")
    typename = hg.BaseElement(fqn(type(field)))
    if field.is_relation:
        if isinstance(field, GenericForeignKey):
            typename.append(f" through ({field.ct_field}, {field.fk_field})")
        else:
            link = hg.SPAN(
                " -> ",
                hg.A(
                    fqn(field.target_field.model),
                    href=utils.reverse(
                        "datamodel",
                        query={
                            "app": field.target_field.model._meta.app_label,
                            "highlight": field.target_field.model.__name__,
                        },
                    ),
                ),
            )
            label.append(link)
    details = hg.DIV(
        hg.CODE(typename),
        style="display: none; padding-left: 1rem; margin-top: 0.25rem",
    )
    return hg.BaseElement(label, details)


def is_same_app_relation(field, currentapp):
    if isinstance(field, GenericForeignKey):
        return False
    if field.is_relation:
        return field.target_field.model._meta.app_label == currentapp
    return False


def fieldlist(model):
    result = []
    for field in model._meta.get_fields():
        if getattr(field, "parent_link", False) is False:
            result.append(field)
    return result


def modelbox(model, highlighted):
    return hg.DIV(
        hg.DIV(
            hg.H5(
                hg.format(
                    "{} {}",
                    model.__name__,
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
                fieldlist(model),
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
            "orange 3px" if model.__name__ == highlighted else "black 1px",
        ),
        id=model.__name__,
        _class="modelbox",
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
    searchfunc = """
for(model of $$(".modelbox h5")) {
    let container = model.closest(".modelbox");
    if(this.value == "") {
        container.style.display = "initial";
        model.style.backgroundColor = "initial";
        for(field of $$("li", container)) {
            field.style.backgroundColor = "initial";
        }
    } else {
        if(model.innerText.toLowerCase().includes(this.value.toLowerCase())) {
            container.style.display = "initial";
            model.style.backgroundColor = "yellow";
        } else {
            container.style.display = "none";
            model.style.backgroundColor = "initial";
            for(field of $$("li", container)) {
                field.style.backgroundColor = "initial";
                if(field.innerText.toLowerCase().includes(this.value.toLowerCase())) {
                    container.style.display = "initial";
                    field.style.backgroundColor = "yellow";
                }
            }
        }
    }
}
"""

    return hg.BaseElement(
        hg.H1("Datamodel"),
        hg.DIV(
            layout.forms.widgets.TextInput(
                inputelement_attrs={
                    "placeholder": _("Search..."),
                    "onkeyup": searchfunc,
                    "style": "box-shadow: 0px 5px 10px gray",
                },
                style="position: sticky; top: 4rem; margin: 0 auto; max-width: 20rem; height: 0;",
            ),
            layout.forms.Form(
                form,
                layout.forms.FormField(
                    "app",
                    onclick="this.closest('form').submit()",
                    no_wrapper=True,
                    style="display: inline-block",
                ),
                method="GET",
            ),
            hg.DIV(
                *[modelbox(m, request.GET.get("highlight")) for m in models],
                style="display: flex; flex-wrap: wrap; align-items: flex-start; margin-top: 1rem; margin-left: -1rem; margin-right: -1rem",
            ),
            style="margin-top: 2rem",
        ),
        hg.SCRIPT(
            hg.mark_safe(
                f"document.getElementById('{request.GET.get('highlight')}').scrollIntoView(scrollIntoViewOptions={{block: 'center'}});"
            )
        ),
    )
