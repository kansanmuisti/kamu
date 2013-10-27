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

@receiver(post_save, sender=DocumentSignature, dispatch_uid="document_signature_activity")
def create_document_signature_activity(sender, **kwargs):
    obj = kwargs['instance']
    doc = obj.doc
    # Authors don't sign their own iniatives. There is enough
    # glory in authorship.
    if doc.author == obj.member:
        return
    sign_act, created = SignatureActivity.objects.get_or_create(signature=obj)

@receiver(post_save, sender=Document, dispatch_uid="document_activity")
def create_document_activity(sender, **kwargs):
    # Create the activity record for document authorship.
    doc = kwargs['instance']
    if doc.author == None:
        return
    if doc.type not in ('mp_prop', 'written_ques'):
        return
    act, created = InitiativeActivity.objects.get_or_create(doc=doc)
    if created:
        return

    date = act.time.date()
    if doc.author != act.member or doc.date != date:
        act.member = doc.author
        act.time = doc.date
        act.save()
