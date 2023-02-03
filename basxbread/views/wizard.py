import htmlgenerator as hg
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .. import layout


def generate_wizard_form(wizardview, wizardtitle, steptitle, formlayout):
    """
    title: Title of the current page
    steps: list of 2-tuples with (step_title, status) where status must be one of ["incomplete", "complete", "current"]
    """

    # needs to be rendered in view of type NamedUrlSessionWizardView in order to work correctly
    def go_back_url(context):
        url = reverse(
            context["request"].resolver_match.view_name,
            kwargs={"step": context["wizard"]["steps"].prev},
        )
        return f"document.location='{url}'"

    steps = []
    for i, (step, formclass) in enumerate(wizardview.get_form_list().items()):
        status = "incomplete"
        if i < wizardview.steps.index:
            status = "complete"
        if step == wizardview.steps.current:
            status = "current"
        steps.append((formclass.title, status))

    return hg.BaseElement(
        hg.H3(wizardtitle),
        hg.H4(steptitle),
        layout.progress_indicator.ProgressIndicator(
            steps,
            style="margin-bottom: 2rem",
        ),
        layout.forms.Form(
            hg.C("wizard.form"),
            layout.forms.Form(
                hg.C("wizard.management_form"),
                layout.forms.FormField("current_step", form="wizard.management_form"),
                standalone=False,
            ),
            formlayout,
            hg.DIV(
                hg.DIV(
                    hg.If(
                        hg.C("wizard.steps.prev"),
                        layout.button.Button(
                            _("Back"),
                            buttontype="secondary",
                            onclick=hg.F(go_back_url),
                        ),
                    ),
                    hg.If(
                        hg.F(
                            lambda c: c["wizard"]["steps"].last
                            == c["wizard"]["steps"].current
                        ),
                        layout.button.Button(
                            _("Complete"), type="submit", style="margin-left: 1rem"
                        ),
                        layout.button.Button(
                            _("Continue"), type="submit", style="margin-left: 1rem"
                        ),
                    ),
                ),
                style="align-items: flex-end",
                _class="bx--form-item",
            ),
        ),
    )
