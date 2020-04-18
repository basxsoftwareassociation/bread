.. breadengine documentation master file, created by
   sphinx-quickstart on Wed Mar  4 14:49:20 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to breadengine's documentation!
=======================================


.. toctree::
   :maxdepth: 3
   :caption: Contents:

   api/modules

Main features
-------------

- Generate list/read/edit/create/delete views from models e.g. ``bread.views.GeneralList.as_view(model=MyModel)``
    - ListViews:
      - Display modelfields (or model properties)
      - Excel export
      - Filter (configurable fields)
      - Sort (Right now only for database fields)
      - Summary for columns
    - FormViews:
      - When specified show inline formsets (aka 1-to-many fields)
      - Render and wrap GenericForeignKey in a form field which queries <fieldname>_choices in order to determine allowed choices for the generic foreign key
      - Add lazy_choices as an attribute to any modelfield in order to apply choices when generating the form (no migration necessary)
        lazy_choices is a function which takes a request object and an instance object in order to generate a dynamic list of choices
      - Add lazy_initial as an attribute to any modelfield in order to apply an initial value when generating the form (no migration necessary)
        lazy_choices is a function which takes a request object and an instance object in order to generate a dynamic default/initial value for a field
- Generate URLs for the views automatically e.g. ``breadengine.urls.generateBREADurls(MyModel)`` (create list, details, create, edit delete views and urls)
- Scan python packages for menu-entries
- Scan python packages for django "registered bread-apps" and hook their urls in to the breadengine
- Scan python packages for django "registered menus"
- Add dynamic preferences settings and render, render all registered dynamic preferences
- Setup ready to use CKEditor
- Setup ready to use django-guardian for row-level permissions


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
