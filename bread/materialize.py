from crispy_forms.bootstrap import Container, ContainerHolder
from crispy_forms.utils import TEMPLATE_PACK, render_field
from django.template.loader import render_to_string


class CollapsibleGroup(Container):
    template = "%s/collapsible-group.html"


class Collapsible(ContainerHolder):
    template = "%s/collapsible.html"

    def render(self, form, form_style, context, template_pack=TEMPLATE_PACK, **kwargs):
        content = ""
        self.open_target_group_for_form(form)

        for group in self.fields:
            group.data_parent = self.css_id
            content += render_field(
                group, form, form_style, context, template_pack=template_pack, **kwargs
            )

        template = self.get_template_name(template_pack)
        context.update({"collapsible": self, "content": content})

        return render_to_string(template, context.flatten())
