import io

import htmlgenerator as hg
from django.apps import apps
from django.core.management import call_command
from django.forms import Form, formset_factory
from django.utils.translation import gettext_lazy as _

from basxbread import layout, utils
from basxbread.layout.components import forms

from .parser import FieldForm, ModelForm, field2formdata, model2formdata

# concept:
# get models and fields from django config? ==> create form
# let user edit form
# detect changes in form
# in form_success:
#     backup model files and database
#     use redbaron to write changes to model file
#     generate migration files
#     run migration

EDITABLE_APP = "customdata"


@utils.aslayout
def test(request):
    data = None
    if request.method == "POST":
        data = request.POST
    modelforms = {}
    for model in apps.get_app_config(EDITABLE_APP).get_models():
        prefix = model._meta.label_lower.replace(".", "-")
        modelforms[model] = [
            ModelForm(data=data, initial=model2formdata(model), prefix=prefix),
            formset_factory(FieldForm, extra=0)(
                data=data,
                initial=[field2formdata(f) for f in model._meta.get_fields()],
                prefix=prefix,
            ),
        ]
    if request.method == "POST":
        made_changes = False
        for model, (modelform, fieldforms) in modelforms.items():
            if modelform.is_valid() and modelform.changed_data:
                modelform.apply_changes(model)
                made_changes = True
            if fieldforms.is_valid():
                for fieldform in fieldforms:
                    if fieldform.changed_data:
                        fieldform.apply_changes(model)
                        made_changes = True
        if made_changes:
            message_out = io.StringIO()
            error_out = io.StringIO()
            # TODO: create migration files manually
            call_command(
                "makemigrations",
                EDITABLE_APP,
                interactive=False,
                stdout=message_out,
                stderr=error_out,
            )
            call_command(
                "migrate",
                EDITABLE_APP,
                interactive=False,
                stdout=message_out,
                stderr=error_out,
            )

    content = hg.DIV(
        *[
            layout.grid.Row(layout.grid.Col(forms.FormField(f)))
            if f == "type"
            else forms.FormField(f)
            for f in FieldForm().fields
        ],
        style=hg.format(
            "display: {}",
            hg.If(
                hg.F(
                    lambda c: c.get(
                        f"{layout.forms.DEFAULT_FORMSET_CONTEXTNAME}_index", -1
                    )
                    == 0
                ),
                "block",
                "none",
            ),
        ),
        id=hg.format(
            "field-{}",
            hg.C(layout.forms.DEFAULT_FORMSET_CONTEXTNAME).prefix,
        ),
        _class="field-formset",
    )

    return hg.DIV(
        hg.SCRIPT(
            hg.mark_safe(
                """
function add_newfield_tab(prefix){
    console.log($("#fieldformset-" + prefix + "-container div:nth-child(1)"));
    let container = $("#fieldformset-" + prefix + "-container div:nth-child(1)");
    let newbutton = $("#fieldformset-" + prefix + "-container div:nth-child(1) button").cloneNode(true);
    let addbutton = container.lastChild;
    let index = parseInt($("#id_" + prefix + "-TOTAL_FORMS").value) - 1
    newbutton.setAttribute("onclick", newbutton.getAttribute("onclick").replace(prefix + "-0", prefix + "-" + index));
    newbutton.innerText = "<New field>";
    container.appendChild(newbutton);
    container.appendChild(addbutton);
}
"""
            )
        ),
        hg.H1("ModelEdit test page"),
        hg.DIV(
            layout.forms.Form(
                Form(),
                hg.DIV(
                    layout.tabs.Tabs(
                        *[
                            layout.tabs.Tab(
                                label=model._meta.verbose_name,
                                content=hg.DIV(
                                    forms.Form(
                                        modelform,
                                        *[
                                            forms.FormField(f)
                                            for f in ModelForm().fields
                                        ],
                                        standalone=False,
                                    ),
                                    hg.H4(_("Fields")),
                                    layout.forms.Formset(
                                        fieldsformset, content=content
                                    ).management_form,
                                    hg.DIV(
                                        layout.tile.Tile(
                                            hg.Iterator(
                                                fieldsformset,
                                                "form",
                                                layout.button.Button(
                                                    hg.C("form").initial.get(
                                                        "name", _("<New field>")
                                                    ),
                                                    buttontype="ghost",
                                                    onclick=hg.format(
                                                        "$$('.field-formset')._.style({{display: 'none'}}); $('#field-{}')._.style({{display: 'block'}})",
                                                        hg.C("form").prefix,
                                                    ),
                                                ),
                                            ),
                                            layout.forms.Formset(
                                                fieldsformset, hg.BaseElement()
                                            ).add_button(
                                                f"#fieldformset-{modelform.prefix}-container div:nth-child(2)",
                                                label=_("Add new field"),
                                                onclick=hg.format(
                                                    "add_newfield_tab('{}')",
                                                    modelform.prefix,
                                                ),
                                                notext=False,
                                            ),
                                            style="display: flex; flex-direction: column",
                                        ),
                                        layout.tile.Tile(
                                            layout.forms.Formset(
                                                fieldsformset, content=content
                                            ),
                                            style="display: flex; flex-direction: column",
                                        ),
                                        id=f"fieldformset-{modelform.prefix}-container",
                                        style="display: grid; grid-template-columns: 20% 80%; column-gap: 5px",
                                    ),
                                ),
                            )
                            for model, (modelform, fieldsformset) in modelforms.items()
                        ]
                    )
                ),
                layout.forms.helpers.Submit(),
            )
        ),
    )
