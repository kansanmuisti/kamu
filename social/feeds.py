from django.db.models import Q

from lifestream.plugins import FeedPlugin
from lifestream.models import Item, Feed, Lifestream
from votes.models import Member

class VihreaPlugin(FeedPlugin):
    MY_NAME = "social.feeds.VihreaPlugin"
    def process(self, entry):
        item = super(VihreaPlugin, self).process(entry)
        item.feed = entry['vihrea_feed']
        return item

    def include_entry(self, entry):
        if not 'vihrea_feed' in entry:
            return False
        ret = super(VihreaPlugin, self).include_entry(entry)
        if not ret:
            return False

        items_count = Item.objects.filter(
            Q(date = entry['published']) | Q(permalink = entry['link'])
        ).filter(
            feed = entry['vihrea_feed']
        ).count()
        return items_count == 0

    def pre_process(self, entry):
        self.include = False
        super(VihreaPlugin, self).pre_process(entry)
        author = entry['author']
        try:
            member = Member.objects.get_with_print_name(author)
        except Member.DoesNotExist:
            print "MP '%s' not found" % author
            return
        ls = self.feed.lifestream
        if ls.content_object != member:
            try:
                ls = Lifestream.objects.for_object(member).get()
            except Lifestream.DoesNotExist:
                print "No Lifestream for MP '%s'" % member.get_print_name()
                return
            try:
                feed = Feed.objects.get(lifestream=ls,
                                        plugin_class_name=self.MY_NAME)
            except Feed.DoesNotExist:
                print "No Feed for MP '%s'" % member.get_print_name()
                return
        else:
            feed = self.feed
        entry['vihrea_feed'] = feed
