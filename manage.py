#!/usr/bin/env python

import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bread.tests.settings")
django.setup()

if __name__ == "__main__":
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
