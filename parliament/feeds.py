from django.db.models.signals import post_save
from django.dispatch import receiver
from parliament.models import *
from social.models import Update

@receiver(post_save, sender=Statement, dispatch_uid="statement_activity")
def create_statement_activity(sender, **kwargs):
    obj = kwargs['instance']
    # Some statements can be from non-MP speakers
    if not obj.member:
        return
    st_act, created = StatementActivity.objects.get_or_create(statement=obj)

@receiver(post_save, sender=Update, dispatch_uid="social_update_activity")
def create_social_update_activity(sender, **kwargs):
    obj = kwargs['instance']
    upd_act, created = SocialUpdateActivity.objects.get_or_create(update=obj)
