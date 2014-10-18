from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from parliament.models.member import Member
from parliament.models.session import Term

class FundingSource(models.Model):
    TYPES = (
        ('co', _('Corporation')),
        ('ind', _('Individual')),
        ('party', _('Party')),
    )
    name = models.CharField(max_length=120, null=True, blank=True)

    class Meta:
        app_label = 'parliament'

class Funding(models.Model):
    TYPES = (
        ('own', _('Own funds')),
        ('co', _('Corporation')),
        ('ind', _('Individual')),
        ('loan', _('Loan')),
        ('u_ind', _('Undefined individuals')),
        ('u_com', _('Undefined communities')),
        ('party', _('Party')),
        ('oth', _('Other')),
    )
    type = models.CharField(max_length=6, choices=TYPES)
    member = models.ForeignKey(Member, db_index=True)
    term = models.ForeignKey(Term)
    source = models.ForeignKey(FundingSource, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        app_label = 'parliament'
        unique_together = (('member', 'term', 'type', 'source'),)
