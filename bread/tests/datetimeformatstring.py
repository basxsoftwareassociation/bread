import datetime
import random

from bread.utils.datetimeformatstring import to_php_formatstr

from django.conf import settings
from django.test import Client, TestCase
from django.utils.dateformat import format


class ToPHPFormatstrTest(TestCase):
    ALL_FORMATS = (
        settings.DATE_INPUT_FORMATS
        + settings.DATETIME_INPUT_FORMATS
        + settings.TIME_INPUT_FORMATS
    )
    RANDOM_ROUNDS = 100

    def test_format_conversion(self):
        max_delta = datetime.datetime.max - datetime.datetime.min

        for _ in range(self.RANDOM_ROUNDS):
            d = datetime.datetime.min + datetime.timedelta(
                days=random.randint(0, max_delta.days),
                seconds=random.randint(0, max_delta.seconds),
                microseconds=random.randint(0, max_delta.microseconds),
            )
            for f in self.ALL_FORMATS:
                if "y" not in f:
                    self.assertEqual(
                        format(d, to_php_formatstr(f)),
                        d.strftime(f),
                        f"({d}): input was {d.strftime(f)} ({f}), output was {format(d, to_php_formatstr(f))} ({to_php_formatstr(f)})",
                    )
