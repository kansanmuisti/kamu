# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_save
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from kamu.cms.models import Item

PLEDGED_SUM_CHOICES = (
    (30, '30€'),
    (40, '40€'),
    (50, '50€'),
    (60, '60€'),
    (70, '70€'),
    (80, '80€'),
    (90, '90€'),
    (100, '100€'),
)

class NewMember(models.Model):
    name = models.CharField(max_length=50, verbose_name=_('Name'))
    email = models.EmailField(_('E-mail'), max_length=75)
    domicile = models.CharField(max_length=30, verbose_name=_('Home city'))
    pledged_sum = models.IntegerField(choices=PLEDGED_SUM_CHOICES, verbose_name=_('Membership fee'), default=30)
    comments = models.TextField(blank=True, verbose_name=_('Comments'))
    public_membership = models.BooleanField(default=True, verbose_name=_('Public membership'))
    reference = models.CharField(max_length=20, blank=False)
    creation_date = models.DateTimeField(auto_now_add=True)
    
    # A method as this should later be handled through cashflow
    def get_reference(self):
        return self.reference

class Reference(models.Model):
    refnum = models.CharField(max_length=20)

# Sends an email notification when someone registers their interest
# to be a beta tester
def email_notification(sender, **kwargs):
    modelobj = kwargs['instance']

    # Someday check if the fields names can be introspected
    # out from the object.
    # Also a template might be nice.
    subject = "New supporting member for Kamu"
    message = """
Information
-----------
"""
    message += "Name: %s\n" % modelobj.name
    message += "E-mail: %s\n" % modelobj.email
    message += "Domicile: %s\n" % modelobj.domicile
    message += "Comments: %s\n" % modelobj.comments
    message += "Public membership: %s\n" % modelobj.public_membership
    send_mail(subject, message, settings.SERVER_EMAIL, [a[1] for a in settings.NOTIFICATIONS])

    reference = modelobj.get_reference()
    content = Item.objects.retrieve_content('joining_email').data
    subject = _("Your membership application for Kansan muisti KAMU ry")
    message = render_to_string('joining/joining_email.txt', {'sum': modelobj.pledged_sum, 'reference': reference, 'content': content})
    send_mail(subject, message, settings.SERVER_EMAIL, [modelobj.email])

post_save.connect(email_notification, sender=NewMember, dispatch_uid="newmembernotify")
