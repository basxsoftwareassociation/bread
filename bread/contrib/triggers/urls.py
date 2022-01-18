from bread.utils import quickregister

from models import Action, SendEmail, Trigger

urlpatterns = []
quickregister(urlpatterns, Trigger)
quickregister(urlpatterns, Action)
quickregister(urlpatterns, SendEmail)
