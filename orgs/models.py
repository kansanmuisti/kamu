from django.db import models
from django.contrib.auth.models import User, Group
from django.template.defaultfilters import slugify

from kamu.votes.models import Session

class Organization(models.Model):
    name = models.CharField(max_length = 50, unique = True)
    url_name = models.SlugField(max_length = 50, unique = True)
    logo = models.ImageField(upload_to = 'images/orgs')
    description = models.TextField()
    info_link = models.URLField()

    def generate_url_name(self):
        return slugify(self.name)

    def get_group_name(self):
        return 'org-' + self.url_name
    def get_group(self):
        return Group.objects.get(name = self.get_group_name())
    def is_admin(self, user):
        if not user.is_authenticated():
            return False
        if user.groups.filter(name = self.get_group_name()).count():
            return True
        else:
            return False

    def save(self, *args, **kwargs):
        if not self.url_name:
            self.url_name = self.generate_url_name()
        super(Organization, self).save(*args, **kwargs)
        try:
                g = Group.objects.get(name = self.get_group_name())
        except Group.DoesNotExist:
                g = Group(name = self.get_group_name())
                g.save()
    def delete(self):
        super(Organization, self).delete()
        Group.objects.get(name = self.get_group_name()).delete()
    def __unicode__(self):
        return self.name

class SessionScore(models.Model):
    SCORE_MAX = 10

    org = models.ForeignKey(Organization)
    session = models.ForeignKey(Session)
    # from -SCORE_MAX to +SCORE_MAX
    score = models.SmallIntegerField()
    rationale = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = (("org", "session"),)

    def __unicode__(self):
        return "%s/%d" % (self.session.plenary_session.name, self.session.number)
