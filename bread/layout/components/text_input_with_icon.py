from htmlgenerator import DIV

from bread.layout.components.icon import Icon
from bread.layout.components.text_input import TextInput


class TextInputWithIcon(TextInput):
    def __init__(self, icon, **attributes):
        super().__init__(**attributes)
        field_wrapper = self[1]
        field_wrapper.attributes["_class"] = (
            field_wrapper.attributes.get("_class", "") + " text-input-with-icon"
        )
        field_wrapper.append(
            DIV(
                Icon(icon),
                _class="text-input-icon",
            )
        )
