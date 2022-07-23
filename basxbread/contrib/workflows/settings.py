from datetime import timedelta

from django.conf import settings

# DETERMINES HOW OFTEN WORKFLOWS WILL BE RUN TO
# TRIGGER AUTOMATED ACTIONS AND DECISIONS
WORKFLOW_BEAT = getattr(settings, "WORKFLOW_BEAT", timedelta(minutes=5))
