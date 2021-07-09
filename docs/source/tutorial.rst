Tutorial
========

In order to get a better understand of how to start building 
web-based database applications with |projectname| we provide
a tutorial. The goal is to write a small multi-user todo-
application from scratch.

Requirements
============

Required software:

- Python >= 3.6
- pip
- git

We will be using Python 3.9 in the tutorial but the choice does
not really matter. The best option is the standard version of your
operating system as long as it is Python 3.6 or higher.

Setup
=====

python3 -m venv .venv
. .venv/bin/activate
pip install git+https://github.com/basxsoftwareassociation/bread.git
django-admin startproject --template .venv/lib/python3.9/site-packages/bread/resource/project_template todo .

In the beginning there was the model
====================================

class ToDo(models.Model):
    what = models.CharField(max_length=255)
    due = models.DateTimeField(null=True)
    done = models.DateTimeField(null=True)
    creator = models.ForeignKey("contrib.User", on_delete=models.CASCADE, related_name="todos")
    created = models.DateTimeField(auto_now_add=True)

A minimal viable product
========================

- hook up urls, add generated views

Tidy things up a bit
=======================

- Displayed columns
- Add and edit views
- Status labels

And action!
===========

- Actions and bulk actions

Multiplayer
===========

- Permissions, roles
- Per-object permissions

Reminders
=========

- Adding tasks

Getting real
============

- production deployment
- nginx
- uwsgi
