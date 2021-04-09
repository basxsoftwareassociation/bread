Quickstart ...
==============

Required tools (assumed to be run on a linux system):

* git
* make
* python3 (with venv, python development files and a build environment)

... with example project (CRM)
------------------------------

A fully functional implementation of a CRM is available through the 
`basxconnect <https://github.com/basxsoftwareassociation/basxconnect>`_
project. In the first part of the quickstart guide we will use this project
to get a customizable CRM up and running very quickly.


.. code-block:: shell

    git clone https://github.com/basxsoftwareassociation/basxconnect_demo.git
    cd basxconnect_demo
    make quickstart_debian
    # alternatively: make quickstart_fedora
    # for other systems follow the instructions inside the Makefile
    . .venv/bin/activate
    ./manage.py runserver

After running the lines above the CRM is available at http://127.0.0.1:8000
and login with the username `demo` and the password `connectdemo`.

... from scratch (Library management)
-------------------------------------

In the second part of the quickstart guide we will go through a the process
of setting up a fresh Django project, adding |project| and defining models and views.

Setup up the basic project structure:

.. code-block:: shell

    mkdir library_demo && cd library_demo
    python3 -m venv .venv
    . .venv/bin/activate
    pip install Django git+https://github.com/basxsoftwareassociation/bread.git
    django-admin startproject librarymanagement .
    django-admin startapp library

This will generate the following directory structure::

    .
    ├── library
    │   ├── admin.py
    │   ├── apps.py
    │   ├── __init__.py
    │   ├── migrations
    │   │   └── __init__.py
    │   ├── models.py
    │   ├── tests.py
    │   └── views.py
    ├── librarymanagement
    │   ├── asgi.py
    │   ├── __init__.py
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py
    └── manage.p

.. note:: TODO: explain librarymanagement/settings.py
.. note:: TODO: define models
.. note:: TODO: define urls
.. note:: TODO: define views/layouts
.. note:: TODO: run project
