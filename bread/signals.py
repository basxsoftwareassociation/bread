import django.dispatch

post_deployment = django.dispatch.Signal(providing_args=[])
