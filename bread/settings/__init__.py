from django.utils.html import mark_safe

# custom unicode symbols
HTML_TRUE = mark_safe("&#x2714;")  # ✔
HTML_FALSE = mark_safe("&#x2716;")  # ✖
HTML_NONE = mark_safe("&empty;")  # ∅

TEXT_FIELD_DISPLAY_LIMIT = 32
