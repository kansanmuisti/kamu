from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse
from django.utils.translation import ugettext as _
from django.shortcuts import render_to_response, get_list_or_404, get_object_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils import simplejson
from sorl.thumbnail import get_thumbnail
from parliament.models import *
from social.models import Update
from httpstatus import Http400
from datetime import date

def show_item(request, plsess, item_nr, subitem_nr=None):
    query = Q(plsess__url_name=plsess) & Q(number=item_nr)
    if subitem_nr is None:
        query &= Q(sub_number__isnull=True)
    else:
        query &= Q(sub_number=subitem_nr)
    item = get_object_or_404(PlenarySessionItem, query)
    return render_to_response('parliament/plenary_item_details.html', {'item': item},
                              context_instance=RequestContext(request))

def show_member(request, member):
    pass

def _get_parliament_activity(request, offset):
    q = Q(nr_votes__gt=0) | Q(nr_statements__gt=0)
    pl_items = list(PlenarySessionItem.objects.filter(q).select_related('plsess')[offset:offset+5])
    for item in pl_items:
        if item.nr_statements:
            st = item.statement_set.all()[0]
            item.statement = st
    act_html = render_to_string('parliament/_plitem_list.html', {'items': pl_items},
                                context_instance=RequestContext(request))

    return {'offset': offset + 5, 'html': act_html}

def get_parliament_activity(request):
    offset = request.GET.get('offset', 0)
    try:
        offset = int(offset)
    except TypeError:
        raise Http400()
    if offset < 0:
        raise Http400()

    data = _get_parliament_activity(request, offset)
    return HttpResponse(simplejson.dumps(data), mimetype="application/json")

def _get_mp_some_activity(request, offset):
    q = Update.objects.filter(feed__in=MemberSocialFeed.objects.all())
    some_query = q.select_related('feed__membersocialfeed')[offset:offset+5]
    some_updates = []
    for upd in some_query:
        d = {}
        feed = upd.feed.membersocialfeed
        mp = feed.member
        d['time'] = upd.created_time
        d['text'] = upd.text
        d['html'] = upd.render_html()
        d['mp_name'] = mp.get_print_name()
        tn = get_thumbnail(mp.photo, '32x48')
        d['mp_portrait'] = tn.url
        d['mp_link'] = mp.get_absolute_url()
        d['mp_party'] = mp.party.name
        some_updates.append(d)
    some_html = render_to_string('parliament/_some_update_list.html',
                                 {'some_updates': some_updates},
                                 context_instance=RequestContext(request))
    return {'offset': offset + 5, 'html': some_html}

def get_mp_some_activity(request):
    offset = request.GET.get('offset', 0)
    try:
        offset = int(offset)
    except TypeError:
        raise Http400()
    if offset < 0:
        raise Http400()

    data = _get_mp_some_activity(request, offset)
    return HttpResponse(simplejson.dumps(data), mimetype="application/json")

def main(request):
    args = {}

    some_data = _get_mp_some_activity(request, 0)
    args['some_html'] = some_data['html']
    args['some_offset'] = some_data['offset']

    parl_data = _get_parliament_activity(request, 0)
    args['parl_act_html'] = parl_data['html']
    args['parl_act_offset'] = parl_data['offset']

    return render_to_response('new_main.html', args,
                              context_instance=RequestContext(request))

def list_sessions(request, year=None, month=None):
    args = {}

    today = date.today()

    if year is None:
      year = today.year
      month = today.month

    args["year"] = year
    args["month"] = month

    return render_to_response('new_sessions.html', args, context_instance=RequestContext(request))
