from django.db import models
from ttp import ttp


class Feed(models.Model):
    TYPE_CHOICES = (
        ('TW', 'Twitter'),
        ('FB', 'Facebook'),
    )
    type = models.CharField(max_length=2, choices=TYPE_CHOICES)
    origin_id = models.CharField(max_length=50, db_index=True)
    interest = models.PositiveIntegerField(null=True)
    picture = models.URLField(null=True, max_length=250)
    account_name = models.CharField(max_length=50, null=True)
    last_update = models.DateTimeField(db_index=True, null=True)
    update_error_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = (('type', 'origin_id'),)

    def update_from_origin(self):
        from social.utils import get_facebook_graph

        assert(self.type == 'FB')
        addr = '%s?fields=picture,likes,about,username' % self.origin_id
        feed_info = get_facebook_graph(addr)
        self.picture = feed_info.get('picture', {}).get('data', {}).get('url', None)
        self.interest = feed_info.get('likes', None)
        return feed_info

    def get_origin_url(self):
        if self.type == 'FB':
            return 'https://www.facebook.com/%s' % self.origin_id
        elif self.type == 'TW':
            return 'https://www.twitter.com/%s' % self.account_name

    def __unicode__(self):
        if self.account_name:
            acc_str = " (%s)" % self.account_name
        else:
            acc_str = ""
        return "%s / id %s%s" % (self.type, self.origin_id, acc_str)


class BrokenFeed(models.Model):
    type = models.CharField(max_length=2, choices=Feed.TYPE_CHOICES)
    origin_id = models.CharField(max_length=100, db_index=True)
    account_name = models.CharField(max_length=100, null=True)
    check_time = models.DateTimeField(auto_now=True)
    reason = models.CharField(max_length=50)

    class Meta:
        unique_together = (('type', 'origin_id'),)


class Update(models.Model):
    feed = models.ForeignKey(Feed, on_delete=models.CASCADE, db_index=True)
    text = models.TextField(null=True)
    type = models.CharField(max_length=30)
    sub_type = models.CharField(max_length=30, null=True)
    created_time = models.DateTimeField(db_index=True)
    origin_id = models.CharField(max_length=50, db_index=True)
    origin_data = models.TextField(null=True, help_text="Raw dump of all data from source")
    interest = models.PositiveIntegerField(null=True)
    picture = models.URLField(null=True, max_length=350)
    share_link = models.URLField(null=True, max_length=350)
    share_title = models.CharField(null=True, max_length=250)
    share_caption = models.CharField(null=True, max_length=600)
    share_description = models.TextField(null=True)

    last_modified_time = models.DateTimeField(db_index=True, auto_now=True, null=True)

    class Meta:
        unique_together = (('feed', 'origin_id'),)
        ordering = ['-created_time']

    def get_origin_url(self):
        if self.feed.type == 'FB':
            return 'https://www.facebook.com/%s' % self.origin_id
        elif self.feed.type == 'TW':
            return 'https://www.twitter.com/%s/status/%s' % (self.feed.account_name, self.origin_id)

    def render_html(self):
        if self.feed.type == 'TW':
            p = ttp.Parser()
            tt = p.parse(self.text)
            return tt.html
        else:
            return self.text

    def __unicode__(self):
        return '%s: %s (%s)' % (self.feed.type, self.created_time, self.feed.account_name)

class ApiToken(models.Model):
    type = models.CharField(max_length=2, choices=Feed.TYPE_CHOICES)
    token = models.CharField(max_length=100)
    updated_time = models.DateTimeField(auto_now=True)
