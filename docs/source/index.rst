.. bread documentation master file, created by
   sphinx-quickstart on Mon Mar 29 21:24:21 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to |project|'s documentation!
=====================================

.. warning:: This documentation is work in progress

|project| is a framework which helps building Django based database applications.
|project| itself does not assume anything about the data model of your application.
Instead it tries to provide common abstractions, shortcus and APIs which can be used
within any Django project. While in some regards similar to :py:mod:`django:django.contrib.admin`
|project| focuses much more on building a complete database system instead of a backend
administration tool for websites. Therefore |project| is *not* API compatible with 
:py:mod:`django:django.contrib.admin`, unlike some other projects
(see `here <https://djangopackages.org/grids/g/admin-interface/>`_).

A core component of |project| is the implementation of a UI system which helps creating
consistent user interfaces. The implementation is based on the
`IBM Carbon Design System <https://djangopackages.org/grids/g/admin-interface/>`_ and provides
most of the official carbon components.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   quickstart
   guide
   concepts
   recepies
   tutorial

.. toctree::
   :maxdepth: 3
   :caption: Reference:

   reference/modules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
