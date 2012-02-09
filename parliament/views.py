from django.db.models import Q
from django.utils.translation import ugettext as _
from django.shortcuts import render_to_response, get_list_or_404, get_object_or_404
from django.template import RequestContext
from sorl.thumbnail.main import DjangoThumbnail
from parliament.models import *
from social.models import Update

def new_main(request):
    args = {}
    q = Update.objects.filter(feed__in=MemberSocialFeed.objects.all())
    some_updates = q.select_related('feed__membersocialfeed')[0:5]
    update_list = []
    for upd in some_updates:
        d = {}
        feed = upd.feed.membersocialfeed
        mp = feed.member
        d['time'] = upd.created_time
        d['text'] = upd.text
        d['mp_name'] = mp.get_print_name()
        tn = DjangoThumbnail(mp.photo, (32, 48))
        d['mp_portrait'] = unicode(tn)
        d['mp_link'] = mp.get_absolute_url()
        update_list.append(d)
    args['some_updates'] = update_list

    q = Q(nr_votes__gt=0) | Q(nr_statements__gt=0)
    pl_items = list(PlenarySessionItem.objects.filter(q)[0:5])
    for item in pl_items:
        if item.nr_statements:
            st = item.statement_set.all()[0]
            item.statement = st

    args['pl_items'] = pl_items

    return render_to_response('new_main.html', args,
                              context_instance=RequestContext(request))
