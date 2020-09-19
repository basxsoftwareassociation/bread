from crispy_forms.utils import TEMPLATE_PACK

from layout.carbon_design import Component


class Tooltip(Component):
    template = "carbon_design/components/tooltip.html"

    def __init__(self, *fields, **kwargs):
        super().__init__(*fields, **kwargs)

    def render(self, form, form_style, context, template_pack=TEMPLATE_PACK, **kwargs):
        return super().render(form, form_style, context, template_pack, **kwargs)
