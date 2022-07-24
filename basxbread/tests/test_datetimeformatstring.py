import datetime
import random

from django.conf import settings
from django.test import TestCase
from django.utils.dateformat import format
from django.utils.translation import activate

from ..layout.components.forms.widgets import to_php_formatstr


class ToPHPFormatstrTest(TestCase):
    ALL_FORMATS = (
        settings.DATE_INPUT_FORMATS
        + settings.DATETIME_INPUT_FORMATS
        + settings.TIME_INPUT_FORMATS
    )
    RANDOM_ROUNDS = 100

    def test_format_conversion(self):
        activate("en")  # datetime.strftime cannot handle locale easily
        max_delta = datetime.datetime.max - datetime.datetime.min

        for _ in range(self.RANDOM_ROUNDS):
            d = datetime.datetime.min + datetime.timedelta(
                days=random.randint(0, max_delta.days),  # nosec
                seconds=random.randint(0, max_delta.seconds),  # nosec
                microseconds=random.randint(0, max_delta.microseconds),  # nosec
            )
            for f in self.ALL_FORMATS:
                # Ignore some cases: Django zero-pads %Y, but Python does not
                # (since Python is using ctime). Django has zero-padding
                # because PHP does, also according to Django docs
                if d.year >= 1000 or "%Y" not in f:
                    self.assertEqual(
                        format(d, to_php_formatstr(f)),
                        d.strftime(f),
                        f"({d}): input was {d.strftime(f)} ({f}), "
                        f"output was {format(d, to_php_formatstr(f))} ({to_php_formatstr(f)})",
                    )
