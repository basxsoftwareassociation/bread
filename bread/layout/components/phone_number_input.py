from htmlgenerator import DIV

from bread.layout.components.icon import Icon
from bread.layout.components.text_input import TextInput


class PhoneNumberInput(TextInput):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self[1].append(
            DIV(
                Icon("phone"),
                _class="text-input-icon",
            )
        )
