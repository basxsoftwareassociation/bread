from bread.utils import quickregister

from .models import DataChangeTrigger, DateFieldTrigger, SendEmail

urlpatterns = []
quickregister(urlpatterns, DataChangeTrigger)
quickregister(urlpatterns, DateFieldTrigger)
quickregister(urlpatterns, SendEmail)
