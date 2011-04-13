from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.db import models

from user_voting.managers import VoteManager

SCORES = (
    (u'+1', +1),
    (u'-1', -1),
    (u'?',   0),
)

class Vote(models.Model):
    """
    A vote on an object by a User.
    """
    user         = models.ForeignKey(User)
    content_type = models.ForeignKey(ContentType)
    object_id    = models.PositiveIntegerField()
    object       = generic.GenericForeignKey('content_type', 'object_id')
    score        = models.SmallIntegerField()
    date         = models.DateTimeField(auto_now=True)

    objects = VoteManager()

    class Meta:
        db_table = 'user_votes'
        # One vote per user per object
        unique_together = (('user', 'content_type', 'object_id'),)

    def __unicode__(self):
        return u'%s: score %d by %s' % (self.object, self.score, self.user)
