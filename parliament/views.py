# -*- coding: utf-8 -*-
import operator
import datetime

from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.db.models import Q, Min, Max, Sum
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
from utils import time_func

import parliament.member_views
from parliament.api import MemberResource, KeywordResource, PartyResource, \
    DocumentResource

FEED_ACTIONS = [
    {
        'name': 'Twitter',
        'icon': 'social-twitter',
        'type': 'TW',
        'action': _('tweeted'),
        'group': 'social'
    }, {
        'name': 'Facebook',
        'icon': 'social-facebook',
        'type': 'FB',
        'action': _('published in Facebook'),
        'group': 'social'
    }, {
        'name': _('Statements'),
        'icon': 'message',
        'type': 'ST',
        'action': _('made a plenary statement'),
        'group': 'parliament'
    }, {
        'name': _('Signatures'),
        'icon': 'edit',
        'type': 'SI',
        'action': _('signed'),
        'action_with_target': {
            'mp_prop': _('signed an initiative'),
            'written_ques': _('signed a written question'),
        },
        'group': 'parliament'
    }, {
        'name': _('Own initiatives'),
        'icon': 'document-add',
        'type': 'IN',
        'action': _('sponsored an initiative'),
        'group': 'parliament'
    }, {
        'name': _('Written questions'),
        'icon': 'info-outline',
        'type': 'WQ',
        'action': _('submitted a written question'),
        'group': 'parliament'
    },
    {
        'name': _('Government bills'),
        'icon': 'clipboard',
        'type': 'GB',
        'action': _('government bill was introduced'),
        'group': 'parliament',
        'no_actor': True,
    }
]

"""
    {
        'name': _('Votes'),
        'icon': 'thumbs-down',
        'type': 'RV',
        'action': _('voted against own party'),
        'group': 'parliament'
    }, {
        'name': _('Dissents'),
        'icon': 'flash',
        'type': 'CD',
        'action': _('submitted a committee dissent'),
        'group': 'parliament'
    },
"""

MEMBER_LIST_FIELDS = [
    {
        'id': 'recent_activity',
        'name': _('Activity'),
    }, {
        'id': 'name',
        'name': _('Name'),
    }, {
        'id': 'attendance',
        'name': _('Attendance'),
    }, {
        'id': 'party_agree',
        'name': _('Agreement with party'),
    }, {
        'id': 'term_count',
        'name': _('Number of terms'),
    }, {
        'id': 'age',
        'name': _('Age'),
    }
]

party_json = None
def get_parties(request):
    global party_json

    if party_json:
        return party_json
    res = PartyResource(api_name='v1')
    request_bundle = res.build_bundle(request=request)
    queryset = res.obj_get_list(request_bundle)

    bundles = []
    for obj in queryset:
        bundle = res.build_bundle(obj=obj, request=request)
        bundles.append(res.full_dehydrate(bundle, for_list=True))
    json = res.serialize(None, bundles, "application/json")
    party_json = json
    return json


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

def _get_member_activity_kws(member):
    kw_act_list = KeywordActivity.objects.filter(activity__member=member).select_related('keyword', 'activity', 'activity__type')
    kw_dict = {}
    for kwa in kw_act_list:
        name = kwa.keyword.name
        score = kwa.activity.type.weight
        if name in kw_dict:
            kw_dict[name] += score
        else:
            kw_dict[name] = score
    kw_list = sorted(kw_dict.iteritems(), key=operator.itemgetter(1), reverse=True)[0:20]
    return kw_list

def make_feed_filters(actor=False):
    groups = {}
    for a in FEED_ACTIONS:
        if actor and a.get('no_actor', False):
            continue
        grp = a['group']
        d = groups.get(grp, [])
        d.append(a)
        groups[grp] = d
    return groups

def make_feed_actions():
    d = {}
    for a in FEED_ACTIONS:
        n = a.copy()
        del n['type']
        d[a['type']] = n
    return d

def show_member(request, member, page=None):
    member = get_view_member(member)
    member.posts = member.get_posts()

    res = MemberResource()
    res_bundle = res.build_bundle(obj=member, request=request)
    member_json = res.serialize(None, res.full_dehydrate(res_bundle), 'application/json')
    args = dict(member=member, member_json=member_json, party_json=get_parties(request))
    activity_types = list(MemberActivityType.objects.all())
    types = [[t.type, _(t.name)] for t in activity_types]
    weights = {t.type: t.weight for t in activity_types}

    max_time = member.memberactivity_set.aggregate(Max("time"))['time__max']
    member_activity_end_date = max_time.date

    args['member_activity_end_date'] = member_activity_end_date
    args['activity_counts_json'] = res.serialize(None,
        member.get_activity_counts(), 'application/json')
    args['activity_types_json'] = res.serialize(None,
        types, 'application/json')
    args['activity_type_weights_json'] = res.serialize(None,
        weights, 'application/json')
    args['feed_filters'] = make_feed_filters(actor=True)
    args['feed_actions_json'] = simplejson.dumps(make_feed_actions(), ensure_ascii=False)
    kw_act = _get_member_activity_kws(member)
    kw_act_json = simplejson.dumps(kw_act, ensure_ascii=False)
    args['keyword_activity'] = kw_act_json
    template = 'member/details.html'

    return render_to_response(template, args,
        context_instance=RequestContext(request))

def _get_parliament_activity(request, offset):
    q = Q(nr_votes__gt=0) | Q(nr_statements__gt=0)
    pl_items = list(PlenarySessionItem.objects.filter(q).select_related('plsess')[offset:offset+5])
    for item in pl_items:
        if not item.nr_statements:
            continue
        st_list = item.statement_set.all().exclude(type='speaker')
        if st_list:
            item.statement = st_list[0]
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


def _get_most_active_mps():
    ret = cache.get('most_active_mps')
    if ret:
        return ret[0:10]
    mp_list = list(Member.objects.current())
    begin = datetime.date.today() - datetime.timedelta(days=30)
    for mp in mp_list:
        mp.score = mp.get_activity_score(begin=begin)
    mp_list = sorted(mp_list, key=lambda x: x.score, reverse=True)
    cache.set('most_active_mps', mp_list, 8*60*60)
    return mp_list[0:10]

def main(request):
    args = {}

    some_data = _get_mp_some_activity(request, 0)
    args['some_html'] = some_data['html']
    args['some_offset'] = some_data['offset']

    parl_data = _get_parliament_activity(request, 0)
    args['parl_act_html'] = parl_data['html']
    args['parl_act_offset'] = parl_data['offset']

    args['most_active_mps'] = _get_most_active_mps()

    navbuttons = [
        {
            'title': 'Aiheet',
            'text': 'Selaa eduskunnan käsittelemiä asioita aihealueittain',
            'image': 'images/etu-asiat-300x200.png',
            'url': reverse('parliament.views.list_topics')
        }, {
            'title': 'Kansan&shy;edustajat',
            'text': 'Tutustu kansanedustajiin ja heidän ajamiinsa asioihin',
            'image': 'images/etu-mpt-300x200.png',
            'url': reverse('parliament.views.list_members')
        }, {
            'title': 'Puolueet',
            'text': 'Mistä eri puolueet ovat kiinnostuneet?',
            'image': 'images/etu-puolueet-300x200.png',
            'url': reverse('parliament.views.list_parties')
        },
    ]
    args['navbuttons'] = navbuttons

    return render_to_response('home.html', args,
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


def get_embedded_resource_list(request, resource, options={}):
    old_GET = request.GET
    request.GET = options
    res = resource(api_name='v1')
    request_bundle = res.build_bundle(request=request)
    queryset = res.obj_get_list(request_bundle)
    queryset = res.apply_sorting(queryset, options)
    if 'limit' in options:
        queryset = queryset[0:int(options['limit'])]

    bundles = []
    for obj in queryset:
        bundle = res.build_bundle(obj=obj, request=request)
        bundles.append(res.full_dehydrate(bundle, for_list=True))
    json = res.serialize(None, bundles, "application/json")

    request.GET = old_GET
    return json

def get_embedded_resource(request, resource, obj, options={}):
    old_GET = request.GET
    request.GET = options

    res = resource(api_name='v1')
    res_bundle = res.build_bundle(obj=obj, request=request)
    json = res.serialize(None, res.full_dehydrate(res_bundle), 'application/json')

    request.GET = old_GET
    return json

def list_topics(request):
    args = {}
    resource = KeywordResource()

    opts = {'limit': 20, 'activity': 'true'}

    opts['since'] = 'month'
    args['recent_topics_json'] = get_embedded_resource_list(request, KeywordResource, opts)

    """
    term_start = Term.objects.latest().begin
    opts['since'] = str(term_start)
    args['term_topics_json'] = get_embedded_resources(request, KeywordResource, opts)

    del opts['since']
    args['all_time_topics_json'] = get_embedded_resources(request, KeywordResource, opts)
    """

    return render_to_response('list_topics.html', args,
        context_instance=RequestContext(request))

def show_topic(request, topic, slug=None):
    # We don't use slug for anything.
    kw = get_object_or_404(Keyword, id=topic)
    kw_json = get_embedded_resource(request, KeywordResource, kw, {'related': '1', 'most_active': '1'})
    args = {'topic': kw, 'keyword_json': kw_json}
    args['feed_actions_json'] = simplejson.dumps(make_feed_actions(), ensure_ascii=False)
    args['feed_filters_json'] = simplejson.dumps(make_feed_filters(), ensure_ascii=False)
    agr = kw.keywordactivity_set.aggregate(Max("activity__time")) 
    max_time = agr['activity__time__max']
    keyword_activity_end_date = max_time.date
    args['keyword_activity_end_date'] = keyword_activity_end_date

    return render_to_response('show_topic.html', args,
        context_instance=RequestContext(request))

def list_members(request):
    args = {}
    args['party_json'] = get_parties(request)
    args['list_fields_json'] = simplejson.dumps(MEMBER_LIST_FIELDS)

    return render_to_response('member/list.html',
            args, context_instance=RequestContext(request))

def get_processing_stages(doc):
    stage_choices = DocumentProcessingStage.STAGE_CHOICES
    stages = doc.documentprocessingstage_set.all()

    doc_stages = []
    def add_stage(stage_id, date):
        d = {'id': stage_id, 'date': date}
        for c in stage_choices:
            if c[0] == stage_id:
                s = c[1]
                s = s.replace('&shy;', '-<br>')
                d['name'] = s
                break
        else:
            raise Exception("Processing stage %s invalid" % stage_id)
        doc_stages.append(d)

    for st in stages:
        add_stage(st.stage, st.date)

    if not doc.type in doc.PROCESSING_FLOW:
        return doc_stages
    flow = doc.PROCESSING_FLOW[doc.type]
    if st.stage not in flow:
        return doc_stages

    idx = flow.index(st.stage)
    for st_id in flow[idx+1:]:
        add_stage(st_id, None)

    return doc_stages

def show_document(request, slug):
    doc = get_object_or_404(Document, url_name=slug)
    if doc.summary:
        doc.summary = doc.summary.replace('\n', '\n\n')
    doc.processing_stages = get_processing_stages(doc)

    session_items = doc.plenarysessionitem_set
    session_items = session_items.select_related("statement_set", "plsess")
    session_items = session_items.filter(nr_statements__gt=0)

    # Praise the power of Django's templates!
    for i in session_items:
        i.statements = []
        for s in i.statement_set.all():
            s.text = s.text.replace('\n', '\n\n')
            i.statements.append(s)

    args = {'doc': doc, 'session_items': session_items}
    args['document_json'] = get_embedded_resource(request, DocumentResource, doc)

    return render_to_response('show_document.html', args,
        context_instance=RequestContext(request))

def list_parties(request):
    return render_to_response('party/list.html', context_instance=RequestContext(request))

def show_party(request, name):
    party = get_object_or_404(Party, name=name)

    party_json = get_embedded_resource(request, PartyResource, party)
    args = dict(party=party, party_json=party_json)

    return render_to_response("party/details.html", args,
        context_instance=RequestContext(request))

def list_party_mps(request, name):
    party = get_object_or_404(Party, name=name)

    party_json = get_embedded_resource(request, PartyResource, party)
    args = dict(party=party, party_json=party_json)
    party_mp_list_json = get_embedded_resource_list(request, MemberResource, {'party': party})
    args['member_list_json'] = party_mp_list_json

    return render_to_response("party/mps.html", args, context_instance=RequestContext(request))
