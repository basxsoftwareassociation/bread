# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

import django
from django.conf import settings

sys.path.insert(0, os.path.abspath("../.."))
import sphinx_rtd_theme  # noqa

from basxbread.tests.settings import HAYSTACK_CONNECTIONS, INSTALLED_APPS  # noqa

settings.configure(  # nosec because this is only for local development
    DEBUG=True,
    USE_TZ=True,
    USE_I18N=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    MIDDLEWARE_CLASSES=(),
    SITE_ID=1,
    INSTALLED_APPS=INSTALLED_APPS,
    AUTHENTICATION_BACKENDS=(
        "django.contrib.auth.backends.ModelBackend",
        "guardian.backends.ObjectPermissionBackend",
    ),
    SECRET_KEY="SECRET_KEY_FOR_TESTING",
    STATIC_URL="static/",
    AJAX_URLPARAMETER="asajax",
    HIDEMENUS_URLPARAMETER="hidemenus",
    HAYSTACK_CONNECTIONS=HAYSTACK_CONNECTIONS,
)

django.setup()

# -- Project information -----------------------------------------------------

project = "*basxBread*"
copyright = "2021, basx Software Association"
author = "basx Software Association"

rst_epilog = ".. |project| replace:: %s" % project


# The full version, including alpha/beta/rc tags
release = "0.3"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx_rtd_theme",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
]
autosummary_generate = True
intersphinx_mapping = {
    "django": (
        "https://docs.djangoproject.com/en/dev",
        "https://docs.djangoproject.com/en/dev/_objects/",
    ),
}


# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
