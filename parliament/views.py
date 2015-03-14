# -*- coding: utf-8 -*-
import datetime
import json

from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.core.cache import cache
from django.db.models import Q, Max, Sum, Count
from django.http import HttpResponse
from django.utils.translation import ugettext as _
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from sorl.thumbnail import get_thumbnail
from parliament.models import *
from social.models import Update
from httpstatus import Http400

from parliament.api import MemberResource, KeywordResource, PartyResource, \
    DocumentResource

FEED_FILTER_GROUPS = {
    'social': _("Social"),
    'parliament': _("Parliament")
}

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
        'id': 'activity_score',
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

MEMBER_LIST_FIELD_CATEGORIES = [
    {
        'id': 'statistics',
        'name': _("Term's statistics"),
        'fields': ['activity_score', 'attendance', 'party_agree']
    },
    {
        'id': 'default',
        'name': _("Basic info")
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

def hack_stuff_to_template_context_because_django_sucks(request):
    return {
            'PARTY_LIST_JSON': get_parties(request)
            }

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

def _get_member_activity_kws(member, since=Term.objects.latest().begin, n=20):
    kw_act_list = (
        Keyword.objects
        .filter(keywordactivity__activity__member=member,
            keywordactivity__activity__time__gte=since)
        .annotate(score=Sum("keywordactivity__activity__type__weight"))
        .order_by('-score')
        )
    
    kw_act_list = kw_act_list[:n]
    
    return [(r.name, r.score) for r in kw_act_list]

def _get_party_activity_kws(party, since=Term.objects.latest().begin, n=20):
    # TODO: Should do on the proper party membership?
    kw_act_list = (
        Keyword.objects
        .filter(keywordactivity__activity__member__party=party,
            keywordactivity__activity__time__gte=since)
        .annotate(score=Sum("keywordactivity__activity__type__weight"))
        .order_by('-score')
        )
    
    kw_act_list = kw_act_list[:n]
    
    return [(r.name, r.score) for r in kw_act_list]

def make_feed_filters(actor=False):
    groups = {}
    for a in FEED_ACTIONS:
        if actor and a.get('no_actor', False):
            continue
        grp = a['group']
        if grp not in groups:
            groups[grp] = {'name': FEED_FILTER_GROUPS[grp], 'items': []}
        groups[grp]['items'].append(a)
    return groups


def add_feed_filters(args, actor=False):
    feed_filters = {
        'buttons': make_feed_filters(actor=actor),
        'groups': FEED_FILTER_GROUPS,
        'disable_button': {
            'label': _('All activities')
        }
    }
    args['feed_filters'] = feed_filters


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
    add_feed_filters(args, actor=True)
    args['feed_actions_json'] = json.dumps(make_feed_actions(), ensure_ascii=False)
    kw_act = _get_member_activity_kws(member)
    kw_act_json = json.dumps(kw_act, ensure_ascii=False)
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
    return HttpResponse(json.dumps(data), mimetype="application/json")

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
        d['mp_party'] = mp.party.abbreviation
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
    return HttpResponse(json.dumps(data), mimetype="application/json")


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

def _get_discussed_topics():
    begin = datetime.date.today() - datetime.timedelta(days=30)
    items = PlenarySessionItem.objects.filter(
        nr_statements__isnull=False,
        plsess__date__gt=begin,
        plenarysessionitemdocument__order=0
        ).order_by('-nr_statements')
    items = items.annotate(keywords_count=Count('docs__keywords'))
    items = items.filter(keywords_count__gt=0)
    items = items[:10]
    discussed_topics = []
    for item in items:
        first_doc = item.docs.all()[0]
        topic = first_doc.keywords.all()[0]
        topic = item.docs.all()[0].keywords.all()[0]
        item_list = item.statement_set.filter(type='normal')
        if item_list:
            first_statement = item_list[0]
        else:
            first_statement = None
        topic.item = item
        topic.first_statement = first_statement
        topic.doc = first_doc
        discussed_topics.append(topic)
    
    return discussed_topics

def main(request):
    args = {}

    parl_data = _get_parliament_activity(request, 0)
    args['parl_act_html'] = parl_data['html']
    args['parl_act_offset'] = parl_data['offset']

    args['discussed_topics'] = _get_discussed_topics()

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


def list_sessions(request):
    return render_to_response('sessions.html', {}, context_instance=RequestContext(request))


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


def show_topic_by_name(request):
    name = request.GET.get('name', '').strip().lower()
    kw = get_object_or_404(Keyword, name__iexact=name)
    url = reverse("parliament.views.show_topic", kwargs=dict(topic=kw.id, slug=kw.get_slug()))
    return redirect(url)


def show_topic(request, topic, slug=None):
    # We don't use slug for anything.
    kw = get_object_or_404(Keyword, id=topic)
    kw_json = get_embedded_resource(request, KeywordResource, kw, {'related': '1', 'most_active': '1'})
    args = {'topic': kw, 'keyword_json': kw_json}
    args['feed_actions_json'] = json.dumps(make_feed_actions(), ensure_ascii=False)
    add_feed_filters(args, actor=True)

    agr = kw.keywordactivity_set.aggregate(Max("activity__time"))
    max_time = agr['activity__time__max']
    keyword_activity_end_date = max_time.date
    args['keyword_activity_end_date'] = keyword_activity_end_date

    return render_to_response('show_topic.html', args,
        context_instance=RequestContext(request))


def list_members(request):
    args = {}
    args['party_json'] = get_parties(request)
    args['list_fields_json'] = json.dumps(MEMBER_LIST_FIELDS)
    args['MEMBER_LIST_FIELD_CATEGORIES'] = json.dumps(MEMBER_LIST_FIELD_CATEGORIES)

    return render_to_response('member/list.html',
            args, context_instance=RequestContext(request))


def get_processing_stages(doc, pl_items):
    stage_choices = DocumentProcessingStage.STAGE_CHOICES
    stages = doc.documentprocessingstage_set.all()
    item_docs = list(PlenarySessionItemDocument.objects.filter(doc=doc))

    doc_stages = []
    def add_stage(stage_id, date):
        d = {'id': stage_id, 'date': date}
        for c in stage_choices:
            if c[0] == stage_id:
                s = c[1]
                s = s.replace('&shy;', '')
                d['name'] = s
                break
        else:
            raise Exception("Processing stage %s invalid" % stage_id)

        for item_doc in item_docs:
            if item_doc.stage == stage_id:
                d['item'] = item_doc.item
                break
        doc_stages.append(d)

    for st in stages:
        add_stage(st.stage, st.date)

    if doc.type not in doc.PROCESSING_FLOW:
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
    for attr_name in ('summary', 'answer', 'question'):
        t = getattr(doc, attr_name)
        if t:
            setattr(doc, attr_name, t.replace('\n', '\n\n'))

    session_items = doc.plenarysessionitem_set.all()
    session_items = session_items.select_related("plsess")

    doc.processing_stages = get_processing_stages(doc, session_items)

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


def show_party_feed(request, abbreviation):
    party = get_object_or_404(Party, abbreviation=abbreviation)

    party_json = get_embedded_resource(request, PartyResource, party)

    max_time = MemberActivity.objects.filter(member__party=party). \
        aggregate(Max("time"))['time__max']
    party_activity_end_date = max_time.date

    kw_act = _get_party_activity_kws(party)
    kw_act_json = json.dumps(kw_act, ensure_ascii=False)

    governing = [gp for gp in GoverningParty.objects.filter(party=party).order_by('-begin') if gp.end != None]

    args = dict(party=party,
                party_json=party_json,
                party_activity_end_date=party_activity_end_date,
                feed_actions_json=json.dumps(make_feed_actions(), ensure_ascii=False),
                keyword_activity = kw_act_json,
                governing=governing)

    add_feed_filters(args, actor=True)

    return render_to_response("party/feed.html", args,
        context_instance=RequestContext(request))


def show_party_mps(request, abbreviation):
    party = get_object_or_404(Party, abbreviation=abbreviation)

    party_json = get_embedded_resource(request, PartyResource, party)
    party_mp_list_json = get_embedded_resource_list(request, MemberResource, {'party': party, 'include': "stats", 'thumbnail_dim': "104x156", 'current': "True"})

    governing = [gp for gp in GoverningParty.objects.filter(party=party).order_by('-begin') if gp.end != None]    

    args = dict(party=party,
                party_json=party_json,
                list_fields_json=json.dumps(MEMBER_LIST_FIELDS),
                governing=governing)

    return render_to_response("party/mps.html", args, context_instance=RequestContext(request))


def show_party_committees(request, abbreviation):
    party = get_object_or_404(Party, abbreviation=abbreviation)

    args = dict(party=party,)

    return render_to_response("party/committee_seats.html", args, context_instance=RequestContext(request))


def search(request):
    q = request.GET.get('q', '').strip()
    args = dict(party_json=get_parties(request), query=q)
    args['feed_actions_json'] = json.dumps(make_feed_actions(), ensure_ascii=False)
    return render_to_response("search.html", args, context_instance=RequestContext(request))
