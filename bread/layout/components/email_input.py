from bread.layout.components.text_input_with_icon import TextInputWithIcon


class EmailInput(TextInputWithIcon):
    def __init__(self, **attributes):
        super().__init__("email", **attributes)
