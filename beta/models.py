# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext as _
from django.db.models.signals import post_save
from django.core.mail import mail_admins
import os

WNT_STR = _('Will not tell')

# Read in the party names to array parties, so that they are not in code
parties = []
partyfile = open(os.path.join(os.path.dirname(__file__), "parties.txt"))
parties.append((-1, WNT_STR))
parties.append((0, _('No affiliation')))
for line in partyfile:
    parties.append((len(parties) - 1, line.strip().decode('utf8')))
parties.append((len(parties) - 1, _('Other')))

class Tester(models.Model):
    AGE_GROUPS = (
        (-1, WNT_STR),
        (0, '15-24'),
        (1, '25-34'),
        (2, '35-44'),
        (3, '45-54'),
        (4, '55-64'),
        (5, '65-'),
    )
    age_group = models.IntegerField(_('Age'), choices=AGE_GROUPS, default=-1)
    GENDERS = (
        (-1, WNT_STR),
        (0, _('Male')),
        (1, _('Female')),
        (2, _('Other')),
    )
    gender = models.IntegerField(_('Gender'), choices=GENDERS, default=-1)
    INCOME_BRACKETS = (
        (-1, WNT_STR),
        (0, '0-500'),
        (1, '501-1000'),
        (2, '1001-1500'),
        (3, '1501-2000'),
        (4, '2001-3000'),
        (5, '3001-4000'),
        (6, '4001-6000'),
        (7, '6001-8000'),
        (8, '8001-'),
    )
    monthly_income = models.IntegerField(_('Monthly income'),
                                         choices=INCOME_BRACKETS, default=-1)
    EDUCATION = (
        (-1, WNT_STR),
        (0, 'Peruskoulu tai vähemmän'),
        (1, 'Ammatillinen koulutus tai lukio'),
        (2, 'Opisto, AMK tai yliopistotutkinto'),
        (3, 'Lisensiaatin tai tohtorin tutkinto'),
    )
    education = models.IntegerField(_('Education'), choices=EDUCATION,
                                    default=-1)
    POL_ACTIVITY = (
        (-1, WNT_STR),
        (0, _('I belong to a party')),
        (1, _('I always vote')),
        (2, _('I have never voted')),
        (3, _('I vote in the communal elections')),
        (4, _('I vote in the parliamentary elections')),
        (5, _('I vote in the presidentiary elections')),
    )
    political_activity = models.IntegerField(_('Political activity'),
                                             choices=POL_ACTIVITY, default=-1)
    COMPUTER_SKILLS = (
        (-1, WNT_STR),
        (0, _('Can facebook')),
        (1, _('Can word process')),
        (2, _('Can code')),
    )
    email = models.EmailField(_('E-mail'), max_length=75)
    party_affiliation = models.IntegerField(_('Party affiliation'),
                                            choices=parties, default=-1)

# Sends an email notification when someone registers their interest
# to be a beta tester
def email_notification(sender, **kwargs):
    modelobj = kwargs['instance']

    # Someday check if the fields names can be introspected
    # out from the object.
    # Also a template might be nice.
    subject = "New beta applicant for KAMU"
    message = """
Background information
----------------------
"""
    message += "E-mail: %s\n" % modelobj.email
    message += "Age: %s\n" % modelobj.get_age_group_display()
    message += "Gender: %s\n" % modelobj.get_gender_display()
    message += "Income: %s\n" % modelobj.get_monthly_income_display()
    message += "Education: %s\n" % modelobj.get_education_display()
    message += """
Subject information
-------------------
"""
    message += "Political activity: %s\n" % modelobj.get_political_activity_display()
    message += "Party affiliation: %s\n" % modelobj.get_party_affiliation_display()
    message += "E-mail: %s\n" % modelobj.email
    mail_admins(subject, message, fail_silently=False)

post_save.connect(email_notification, sender=Tester)
