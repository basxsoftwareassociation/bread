Concepts
========

There are have a few design decision been made which influence how this framework is structured and why some parts have been implemented with a certain (maybe non-standard or seemingly less convenient) approach. This chapter tries to list most of them and for |project| developers it might be insightfull to read this.

.. note:: TODO See below


.. note:: Even though |project| is labeling itself to be a *framework* and even though the underlying web-application system, Django, is a *framework*, |project| tries to act much more as a *library*. Utilities, compononents and functionallity of the framework should be "inserted" into or "called" from inside the application code instead of the framework "calling" or "wrapping" the application code. This is of course not always possible but it is a general line-of-thought which |project| wants to align with.

B-R-E-A-D-Models
----------------

.. note:: TODO
.. note:: (browse, read, edit, add, delete operations for most database objects, completely free database structure, no models from the framework, or only generic usable models in contrib packages)

URLs
----

|project| requires all URLs to be registered with the "manual" way of Django.
Another approach would be to automatically collect and generate all URLs.
This has been tried in previous versions of the project but turned out to have more disadvantages than advantages.
The following problems occured when generating URLs automatically:

- Accidentally having views available which are not supposed to exists
- Problems during application startup of Django (URLs need to be defined very early in the starting process)
- Harder to debug and hardere to inspect all available URLs

However, in order to make the URL-registration process as easy as possible there are shortcuts which help to reduce the URL registration boilerplate.

.. note:: TODO Add link to documentation

DOM on the server side
----------------------

Django, like most other server side web frameworks, comes with a solid HTML template language included.
Standard Python HTML templating system are almost always conceptually "improved string-interpolation", as is Django's.
This works well with single-purpose web applications and database projects.
However, for a component-based interface framework as |project| wants to offer, this approach does not have enough flexibility.
In order to allow easy customization of UI components, string-interpolation is not enough.
It is not predictable how e.g. a certain UI component needs to be stylized or positioned in a certain context.
Much more the structure of the UI should be expressed in Python objects which allows for modifying and inspecting the UI while handling a request.
The requirements for |project|'s HTML generating system are therefore much closer to that of traditional Desktop UIs or browser front-end frameworks.

For this reason |project| uses `htmlgenerator <https://github.com/basxsoftwareassociation/htmlgenerator>`_.
``htmlgenerator`` allows the construction of web interfaces on the server side directly with python objects.
It is helpful to have an understanding of how the DOM, tree data structures and graphs in general work in order to get the most out of this concept.
The structure of a ``htmlgenerator`` element is a tree of python objects which map either directly to HTML elements or higher-level interface components which are composed of HTML elements.
The tree can be constructed and modified as desired while the database is serving a request.
At some point the tree needs to be serialized and a render method converts it to a single HTML document string.
Rendering (or serialization) of the tree happens lazy and should be rather performant.
Benchmarks still have to done though.

A lot of focus inside |project| is put into creating reusable, high-level UI components which can easily be reused in different database applications. The "DOM on the server side" approach helps a lot in achieving this.


Client side
-----------

Modern front-end frameworks for browsers tend to be rather complex.
Also, for database-heavy application the business logic needs to be replicated to some degree on the front-end.
In order to avoid these front-end complexities and especially for reducing the need of writing synchronization and business logic code on the front-end |project| tries to always package front-end functionality in components which are generated on the server side.
The vanilla Javascript implementation of the UI framework, Carbon Design, is also well prepared for this approach.

Most |project| components can simply be declared on the server side and will then render to encapsulated front-end widgets.
In order to make writting front-end code a bit more lightweight |project| uses `bliss <https://blissfuljs.com/>`_ for manipulating the DOM on the front-end and `htmx <https://htmx.org/>`_ for dynamic content and communication with server endpoints.
These frameworks are not required to be used but it is recommended to be familiar with them and use them when working on front-end matters.

Customizations
--------------

Allowing the customizations of the framework's behaviour and components is an integral part of |project|.
Other frameworks often offer a hook-system which allows for plugins to overwrite specific behaviours.
|project| does currently not have a plugin system and therefore does not work with such a hook system.
This aligns again with the "library-not-framework" concept.
It also means, that there is not a need for strongly structured customization system since every |project| application will be built on the basis of a surrounding Django project which already allows and even requires essential parts of the customization.

These essential parts on the Django side are as follows:

* Django settings (database connections, security settings, custom settings values, etc.)
* Django apps (URL overriding, custom models and views)
* Django signals (react on certain application events)

Further and more granular customization can be done through the following concepts:

* Parameterizing and specializing views (especially the ones provided by |project|)
* Monkey patching (modifying specific variables, classes and functions during runtime or, most likely, during application start)

.. note:: TODO Add link to documentation with code examples
