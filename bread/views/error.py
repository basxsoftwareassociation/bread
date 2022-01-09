from django.http import HttpResponseNotFound
from django.shortcuts import render

from bread.layout import error as layouts
from bread.utils import aslayout


def view404(request, exception):
    return HttpResponseNotFound(layouts.layout404(request))
