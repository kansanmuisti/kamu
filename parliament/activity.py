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
    # Also ignore speaker statements when it comes to activity
    if obj.type == "speaker":
        return   
    act, created = StatementActivity.objects.get_or_create(statement=obj)
    if not created and getattr(obj, '_updated', False):
        act.save()

@receiver(post_save, sender=Update, dispatch_uid="social_update_activity")
def create_social_update_activity(sender, **kwargs):
    obj = kwargs['instance']
    act, created = SocialUpdateActivity.objects.get_or_create(update=obj)
    if not created and getattr(obj, '_updated', False):
        act.save()

@receiver(post_save, sender=DocumentSignature, dispatch_uid="document_signature_activity")
def create_document_signature_activity(sender, **kwargs):
    obj = kwargs['instance']
    doc = obj.doc
    # Authors don't sign their own iniatives. There is enough
    # glory in authorship.
    if doc.author == obj.member:
        return
    act, created = SignatureActivity.objects.get_or_create(signature=obj)
    if not created and getattr(obj, '_updated', False):
        act.save()

@receiver(post_save, sender=Document, dispatch_uid="document_activity")
def create_document_activity(sender, **kwargs):
    # Create the activity record for document authorship.
    obj = kwargs['instance']
    if obj.type not in ('mp_prop', 'written_ques', 'gov_bill'):
        return
    if obj.author == None and obj.type != 'gov_bill':
        return
    act, created = InitiativeActivity.objects.get_or_create(doc=obj)
    if not created and getattr(obj, '_updated', False):
        date = act.time.date()
        act.member = obj.author
        act.time = obj.date
        act.save()
