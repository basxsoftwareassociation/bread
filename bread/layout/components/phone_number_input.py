from bread.layout.components.text_input import TextInput


class PhoneNumberInput(TextInput):
    def __init__(self, **attributes):
        super().__init__("phone", **attributes)
