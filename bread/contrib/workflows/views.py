import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from bread import layout, views


class WorkflowBrowseView(views.BrowseView):
    rowclickaction = "edit"

    def get_layout(self):
        workflow_diagram = layout.modal.Modal(
            _("Workflow Diagram"),
            self.model.workflow_as_svg(),
            label=self.model._meta.verbose_name,
        )

        ret = super().get_layout()
        ret[0][0].append(
            layout.button.Button(
                _("Explain Workflow"),
                **workflow_diagram.openerattributes,
                small=True,
                style="float: right",
                buttontype="tertiary"
            ),
        )
        ret.append(workflow_diagram)
        return ret


class WorkflowEditView(views.EditView):
    def get_layout(self):
        fields = hg.BaseElement(
            *[layout.form.FormField(f) for f in self.object.active_fields()]
        )
        return hg.DIV(
            hg.DIV(
                layout.form.Form.wrap_with_form(hg.C("form"), fields),
                style="flex-grow: 1",
            ),
            hg.DIV(self.object.as_svg(), style="width: 40%"),
            style="display: flex",
        )


class WorkflowEditFullView(views.EditView):
    def get_layout(self):
        return hg.DIV(
            hg.DIV(
                super().get_layout(),
                style="flex-grow: 1",
            ),
            hg.DIV(self.object.as_svg(), style="width: 40%"),
            style="display: flex",
        )
