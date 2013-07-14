import operator

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
from calendar import Calendar
from datetime import date
from dateutil.relativedelta import relativedelta

import parliament.member_views
from parliament.api import MemberResource

def show_item(request, plsess, item_nr, subitem_nr=None):
    query = Q(plsess__url_name=plsess) & Q(number=item_nr)
    if subitem_nr is None:
        query &= Q(sub_number__isnull=True)
    else:
        query &= Q(sub_number=subitem_nr)
    item = get_object_or_404(PlenarySessionItem, query)
    return render_to_response('parliament/plenary_item_details.html', {'item': item},
                              context_instance=RequestContext(request))

def get_view_member(url_name):
    member = get_object_or_404(Member, url_name=url_name)
    current_district = member.districtassociation_set.order_by('-begin')[0].district
    member.current_district = current_district
    return member

def render_member_activity(item):
    d = {'time': item.time}
    if item.type == 'FB':
        # Facebook update
        d['type'] = _('Facebook update')
        d['icon'] = 'facebook'
        o = item.socialupdateactivity.update
        d['text'] = o.text
    elif item.type == 'TW':
        d['type'] = _('Tweet')
        d['icon'] = 'twitter'
        o = item.socialupdateactivity.update
        d['text'] = o.text
    elif item.type == 'ST':
        d['type'] = _('Statement')
        d['icon'] = 'comment-alt'
        o = item.statementactivity.statement
        d['text'] = o.text
    elif item.type == 'IN':
        d['type'] = _('Initiative')
        d['icon'] = 'lightbulb'
        o = item.initiativeactivity.doc
        d['text'] = o.summary
    elif item.type == 'SI':
        d['type'] = _('Signature')
        d['icon'] = 'pencil'
        o = item.signatureactivity.signature.doc
        d['text'] = o.summary
    elif item.type == 'WQ':
        d['type'] = _('Written question')
        d['icon'] = 'question'
        o = item.initiativeactivity.doc
        d['text'] = o.summary
    else:
        return None
    d['text'] = d['text'].replace('\n', '\n\n')
    return d

def _get_member_activity(member, offset):
    items = list(MemberActivity.objects.filter(member=member).order_by('-time'))[offset:offset+10]
    items_out = []
    for item in items:
        i = render_member_activity(item)
        if not i:
            continue
        items_out.append(i)

    return items_out

def _get_member_activity_kws(member):
    kw_act_list = KeywordActivity.objects.filter(activity__member=member).select_related('keyword', 'activity')
    kw_dict = {}
    for kwa in kw_act_list:
        name = kwa.keyword.name
        score = MemberActivity.WEIGHTS[kwa.activity.type]
        if name in kw_dict:
            kw_dict[name] += score
        else:
            kw_dict[name] = score
    kw_list = sorted(kw_dict.iteritems(), key=operator.itemgetter(1), reverse=True)[0:20]
    return kw_list

def show_member(request, member, page=None):
    member = get_view_member(member)
    res = MemberResource()
    res_bundle = res.build_bundle(obj=member, request=request)
    member_json = res.serialize(None, res.full_dehydrate(res_bundle), 'application/json')
    args = dict(member=member, member_json=member_json)

    if not page:
        args['activity'] = _get_member_activity(member, 0)
        kw_act = _get_member_activity_kws(member)
        kw_act_json = simplejson.dumps(kw_act, ensure_ascii=False)
        args['keyword_activity'] = kw_act_json
        template = 'member/overview.html'
    elif page == 'basic-info':
        template = 'member/basic_info.html'
    else:
        raise Http404()

    return render_to_response(template, args,
        context_instance=RequestContext(request))


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
    else:
        year = int(year)
        month = int(month)

    current = date(year, month, 1)
    nextmonth = current + relativedelta(months=1)
    prevmonth = current - relativedelta(months=1)

    args["year"] = year
    args["month"] = month
    args["current"] = current
    args["prevmonth"] = prevmonth
    args["nextmonth"] = nextmonth

    cal = Calendar()
    days = cal.monthdatescalendar(year, month)

    q = Q(nr_votes__gt=0) | Q(nr_statements__gt=0)
    date_q = Q(plsess__date__gte=current, plsess__date__lte=nextmonth)
    pl_items = PlenarySessionItem.objects.filter(q & date_q).select_related('plsess').order_by('plsess__date')

    acc = {}

    for pl_item in pl_items:
        statements, votes, plsess = acc.setdefault(pl_item.plsess.date, (0, 0, None))

        statements += pl_item.nr_statements
        votes += pl_item.nr_votes
        plsess = pl_item.plsess.url_name

        acc[pl_item.plsess.date] = statements, votes, plsess

    def _date_to_info(d):
        info = {}
        info['date'] = d
        info['weekdayclass'] = "small" if d.weekday() in [5, 6] else "normal"
        info['today'] = d == today
        info['offmonth'] = d.month != current.month or d.year != current.year

        statements, votes, plsess = acc.setdefault(d, (0, 0, None))
        info["statements"] = statements
        info["votes"] = votes
        info["plsess"] = plsess

        return info

    args["weeks"] = map(lambda w: map(_date_to_info, w), days)

    return render_to_response('new_sessions.html', args, context_instance=RequestContext(request))

def show_session(request, plsess):
    args = {}
    return render_to_response('new_session.html', args, context_instance=RequestContext(request))

def list_members(request):
    return parliament.member_views.list_members(request)
