import htmlgenerator as hg
from django.forms import formset_factory
from django.urls import path

from basxbread import layout
from basxbread.layout.components import forms
from basxbread.utils import aslayout

from .parser import FieldForm, ModelForm, parse


@aslayout
def test(request):

    with open(
        "/home/sam/p/pythonpackages/bread/basxbread/contrib/reports/models.py"
    ) as f:
        print(parse(f.read()))

    modelforms = {
        "a1": [ModelForm(prefix="a1"), formset_factory(FieldForm)(prefix="a1")],
        "a2": [ModelForm(prefix="a2"), formset_factory(FieldForm)(prefix="a2")],
    }
    return hg.DIV(
        hg.H1("ModelEdit test page"),
        hg.Iterator(
            modelforms.keys(),
            "modelname",
            layout.button.Button(
                hg.C("modelname"),
                onclick=hg.format(
                    "$$('.modelform')._.style({{ 'display': 'none' }}) ; $('#model-{}')._.style({{'display': 'block'}})",
                    hg.C("modelname"),
                ),
            ),
        ),
        hg.Iterator(
            modelforms.items(),
            "modelform",
            hg.DIV(
                forms.Form(
                    hg.C("modelform")[1][0],
                    *[forms.FormField(f) for f in ModelForm().fields]
                ),
                forms.Formset.as_plain(
                    hg.C("modelform")[1][1],
                    content=hg.DIV(
                        *[forms.FormField(f) for f in FieldForm().fields],
                        style="background-color: #fff"
                    ),
                ),
                id=hg.format("model-{}", hg.C("modelform")[0]),
                style="display: none",
                _class="modelform",
            ),
        ),
    )


urlpatterns = [
    path("test", test),
]
