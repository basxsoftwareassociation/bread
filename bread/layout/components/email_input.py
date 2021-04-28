from htmlgenerator import DIV

from bread.layout.components.icon import Icon
from bread.layout.components.text_input import TextInput


class EmailInput(TextInput):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        icon = DIV(
            Icon("email"),
            _class="text-input-icon",
        )
        self[1].append(icon)
