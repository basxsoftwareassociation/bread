from bread.layout.components.text_input_with_icon import TextInputWithIcon


class PhoneNumberInput(TextInputWithIcon):
    def __init__(self, **attributes):
        super().__init__("phone", **attributes)
