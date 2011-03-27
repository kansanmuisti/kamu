from django.http import Http404, HttpResponse
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.conf import settings
from django.shortcuts import render_to_response, get_list_or_404, get_object_or_404
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.db.models import Q, Count
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe
from django.utils import simplejson
from django.utils.http import urlencode, http_date
from django.contrib.auth.decorators import login_required
from django.contrib.csrf.middleware import csrf_exempt
from django.contrib.contenttypes.models import ContentType
from httpstatus.decorators import postonly
from tagging.models import Tag
from tagging.utils import parse_tag_input
from kamu.votes.models import *
from kamu.orgs.models import Organization, SessionScore
from kamu.votes.index import complete_indexer
from sorl.thumbnail.main import DjangoThumbnail
from kamu.contact_form.views import contact_form
from httpstatus import Http400
from user_voting.models import Vote as UserVote
from kamu.opinions.models import Answer

from kamu.cms.models import Item, Newsitem

import time
import djapian
import operator
import datetime
import random

PERIOD_DASH = u'\u2013'
PERIODS = [
    {'name': '2007'+PERIOD_DASH+'2010',   'begin': '2007-03-21', 'end': None,
     'query_name': '2007-2010'},
    {'name': '2003'+PERIOD_DASH+'2006',   'begin': '2003-03-19', 'end': '2007-03-20',
     'query_name': '2003-2006'},
    {'name': '1999'+PERIOD_DASH+'2002',   'begin': '1999-03-24', 'end': '2003-03-18',
     'query_name': '1999-2002'},
]

TERM_KEY = 'term'
DISTRICT_KEY = 'district'
COUNTY_KEY = 'county'

THUMBNAIL_WIDTH_LIMITS = (24,80)
THUMBNAIL_HEIGHT_LIMITS = (24,80)

term_list = list(Term.objects.visible())

def find_term(request):
    """Return the active term for the request."""
    chosen_term = None
    if TERM_KEY in request.GET:
        term = request.GET[TERM_KEY]
        for t in term_list:
            if t.name == term:
                chosen_term = t
                break
    if chosen_term:
        request.session[TERM_KEY] = chosen_term.name
    elif TERM_KEY in request.session:
        term = request.session[TERM_KEY]
        for t in term_list:
            if t.name == term:
                chosen_term = t
                break
    # Choose default if another term is not specifically requested.
    if not chosen_term:
        chosen_term = term_list[0]
    return chosen_term

def find_period(request):
    term = find_term(request)
    return (term.begin, term.end)

def find_district(request, begin, end):
    da_list = DistrictAssociation.objects.list_between(begin, end)

    district = None
    if COUNTY_KEY in request.GET:
        if DISTRICT_KEY in request.session:
            del request.session[DISTRICT_KEY]
        county_name = request.GET[COUNTY_KEY];
        if county_name != u'All counties':
            try:
                county = County.objects.get(name=county_name)
                district = county.get_district_name()
            except County.DoesNotExist:
                pass
    elif DISTRICT_KEY in request.GET:
        district = request.GET[DISTRICT_KEY]

    if district:
        if district == 'all':
            if DISTRICT_KEY in request.session:
                del request.session[DISTRICT_KEY]
            return None
        if district in da_list:
            request.session[DISTRICT_KEY] = district
            return district

    if DISTRICT_KEY in request.session:
        district = request.session[DISTRICT_KEY]
        if district in da_list:
            return district

def generate_row_html(row):
    html = '\t<tr>'
    for val in row:
        if not val:
            html += '<td></td>'
            continue
        html += '<td class="%s"' % (val['class'])
        if 'title' in val:
            html += ' title="%s">' % (val['title'])
        else:
            html += '>'
        if 'link' in val:
            html += '<a href="%s">' % (val['link'])
        if 'img' in val:
            tn = DjangoThumbnail(val['img'], val['img_dim'].split('x'))
            html += '<img src="%s" alt="%s" />' % (unicode(tn), val['img_alt'])
        elif 'value' in val:
            html += val['value']
        if 'link' in val:
            html += '</a>'
        html += '</td>'
    html += '</tr>\n'
    return mark_safe(html)

def generate_header_html(hdr):
    def gen_attrs(item, add_title=True):
        s = ''
        if 'class' in item:
            s += ' class="%s"' % (item['class'])
        if 'id' in item:
            s += ' id="%s"' % (item['id'])
        if 'title' in item and add_title:
            s += ' title="%s"' % (item['title'])
        return s
    html = '\t<tr'
    html += gen_attrs(hdr) + '>'
    for col in hdr['cols']:
        is_image = 'img' in col
        # If the header has an image, set the title on the image
        # component itself.
        html += '<th%s>' % (gen_attrs(col, add_title=not is_image))
        if 'link' in col:
            html += '<a href="%s">' % (col['link'])
        if 'img' in col:
            if 'no_tn' in col and col['no_tn']:
                img_src = settings.MEDIA_URL + col['img']
            else:
                img_src = DjangoThumbnail(col['img'], col['img_dim'].split('x'))
                img_src = unicode(img_src)
            if 'title' in col:
                title = 'title="%s" ' % (col['title'])
            else:
                title = ''
            html += '<img src="%s" %s/>' % (img_src, title)
        else:
            html += col['name']
        if 'link' in col:
            html += '</a>'
        html += '</th>'
    html += '</tr>\n'
    return mark_safe(html)

def generate_modified_query(request, mod_key, mod_val, remove=[]):
    params = dict(request.GET.items())
    for k in remove:
        if k in params:
            del params[k]
    params[mod_key] = mod_val
    return request.path + '?%s' % urlencode(params)

def set_user_vote(request, obj):
    if not 'vote' in request.POST:
        raise Http400
    vote = request.POST['vote'].lower()
    vote_names = ('up', 'down', 'clear')
    vote_values = (1, -1, None)
    if vote not in vote_names:
        raise Http400

    UserVote.objects.record_vote(obj, request.user,
                                 vote_values[vote_names.index(vote)])

    counts = {}
    counts['up'] = UserVote.objects.get_count(obj, 1)
    counts['down'] = UserVote.objects.get_count(obj, -1)
    json = simplejson.dumps(counts)

    return HttpResponse(json, mimetype='application/json')


def list_plsessions(request):
    (date_begin, date_end) = find_period(request)
    pl_list = PlenarySession.objects.between(date_begin, date_end).order_by('-date')
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    paginator = Paginator(pl_list, 25)
    try:
        session_page = paginator.page(page)
    except (EmptyPage, InvalidPage):
        session_page = paginator.page(paginator.num_pages)

    data_dict = { 'pl_session_page': session_page }
    data_dict['switch_term'] = True

    data_dict['active_page'] = 'plsessions'

    return render_to_response('plsessions.html', data_dict,
                              context_instance = RequestContext(request))

def list_sessions(request):
    (date_begin, date_end) = find_period(request)
    # Get only PlenarySessions with at least one voting session
    query = Session.objects.between(date_begin, date_end)
    pl_list = query.distinct().values_list('plenary_session', flat=True)
    # FIXME: Maybe a better way?
    # http://www.djangoproject.com/documentation/models/many_to_one/

    query = PlenarySession.objects.filter(name__in=pl_list)

    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    pl_session_list = query.order_by('-date')
    paginator = Paginator(pl_session_list, 15)
    try:
        session_page = paginator.page(page)
    except (EmptyPage, InvalidPage):
        session_page = paginator.page(paginator.num_pages)

    for pl_sess in session_page.object_list:
        sess_list = Session.objects.filter(plenary_session = pl_sess).order_by('number')
        for ses in sess_list:
                ses.count_votes()
                ses.info = ses.info.replace("\n", "\n\n")
        pl_sess.sess_list = sess_list

    data_dict = { 'pl_session_page': session_page }
    data_dict['switch_term'] = True

    data_dict['active_page'] = 'sessions';

    return render_to_response('sessions.html', data_dict,
                              context_instance = RequestContext(request))

def search_by_keyword(request):
    if not 'query' in request.GET:
        raise Http404()
    kw = get_object_or_404(Keyword, name=request.GET['query'])
    sess_ids = SessionKeyword.objects.filter(keyword=kw).values_list('session', flat=True)
    sess_list = Session.objects.filter(id__in=sess_ids).order_by('-plenary_session__date')

    args = {'sess_list': sess_list, 'keyword': kw}

    return render_to_response('search_keyword.html', args,
                              context_instance=RequestContext(request))

def get_admin_orgs(user, org_name=None):
    groups = user.groups.filter(name__startswith='org-')
    names = [grp.name[4:] for grp in groups]
    orgs = Organization.objects.filter(url_name__in=names)
    return orgs

def generate_score_table(request, session):
    # FIXME
    return None

    scores = SessionScore.objects.filter(session=session).select_related('org')
    user = request.user
    admin_orgs = []
    if user.is_authenticated():
        # Add the links for scoring this session
        admin_orgs = get_admin_orgs(user)
    if not scores and not admin_orgs:
        return None
    tbl = {}
    col_hdr = []
    col_hdr.append({ 'name': '' })  # Logo
    col_hdr.append({ 'name': _('Organization'), 'class': 'td_text' })
    col_hdr.append({ 'name': _('Score') })
    col_hdr.append({ 'name': '' })  # Admin scoring link
    tbl['header'] = col_hdr

    def make_row(org, score, admin):
        row = []
        kwargs = { 'org': org.url_name }
        org_link = reverse('orgs.views.show_org', kwargs=kwargs)
        row.append({ 'img': org.logo, 'img_alt': 'logo', 'img_dim': '32x32',
            'title': org.name, 'link': org_link })
        row.append({ 'value': org.name, 'link': org_link, 'class': 'td_text' })
        if score:
            row.append({ 'value': score.score, 'class': 'td_number' })
        else:
            row.append({ 'value': '' })
        if admin:
            kwargs = { 'org': org.url_name }
            kwargs['plsess'] = session.plenary_session.url_name
            kwargs['sess'] = session.number
            adm_link = reverse('orgs.views.modify_score', kwargs=kwargs)
            row.append({ 'link': adm_link, 'value': _('Modify') })
        return row

    rows = []
    admin_orgs = list(admin_orgs)
    for score in scores:
        org = score.org
        # FIXME: Does this actually work?
        if score.org in admin_orgs:
            admin = True
            admin_orgs.remove(score.org)
        else:
            admin = False
        rows.append(make_row(org, score, admin))
    for org in admin_orgs:
        rows.append(make_row(org, None, True))
    tbl['body'] = rows
    return tbl

def show_session_basic(request, session, psess):
    sort_key = request.GET.get('sort')
    if sort_key and sort_key[0] == '-':
        sort_key = sort_key[1:]
        sort_reverse = True
    else:
        sort_reverse = False
    if sort_key not in ('name', 'party', 'vote'):
        sort_key = 'vote'

    if sort_key == 'name':
        order = 'member__name'
    elif sort_key == 'party':
        order = 'member__party'
    elif sort_key == 'vote':
        order = 'vote'
        sort_reverse = not sort_reverse

    if sort_reverse:
        order = '-' + order

    session.info = session.info.replace('\n', '\n\n')

    district = find_district(request, psess.date, psess.date)
    if district:
        query = Vote.objects.in_district(district, psess.date, psess.date)
    else:
        query = Vote.objects.all()
    query &= query.filter(session = session).order_by(order, 'member__name')
    votes = query.select_related('member', 'member__party')
    session.docs = SessionDocument.objects.filter(sessions=session)
    session.kw_list = session.sessionkeyword_set.values_list('keyword__name', flat=True).order_by('keyword__name')
    for doc in session.docs:
        if doc.summary:
            session.summary = doc.summary.replace('\n', '\n\n')
            break

    score_table = generate_score_table(request, session)

    tables = [{}, {}]
    col_hdr = []
    for t in tables:
        col_hdr = []
        col_hdr.append({ 'name': _('Party'), 'sort_key': 'party', 'class': 'vote_list_party' })
        col_hdr.append({ 'name': '' })
        col_hdr.append({ 'name': _('Name'), 'sort_key': 'name', 'class': 'vote_list_name' })
        col_hdr.append({ 'name': _('Vote'), 'sort_key': 'vote', 'class': 'vote_list_vote' })
        t['col_hdr'] = col_hdr

    def fill_cols(vote):
        row = []
        mem = vote.member
        if mem.party:
            row.append({'img': mem.party.logo, 'img_alt': 'logo', 'img_dim': '24x24',
                        'title': mem.party.full_name, 'class': 'vote_list_party' })
        else:
            row.append(None)
        row.append({'img': mem.photo, 'img_alt': 'portrait', 'img_dim': '24x36',
                'class': 'vote_list_portrait'})
        row.append({'value': mem.name, 'link': '/member/' + mem.url_name + '/',
                'class': 'vote_list_name'})
        if vote.vote == 'Y':
            c = 'yes_vote'
            t = _('Yay')
        elif vote.vote == 'N':
            c = 'no_vote'
            t = _('Nay')
        elif vote.vote == 'E':
            c = 'empty_vote'
            t = _('Empty')
        elif vote.vote == 'A':
            c = 'absent_vote'
            t = _('Absent')
        else:
            c = ''
            t = ''
        row.append({'title': t, 'class': c})
        return row

    middle = (len(votes) + 2) / 2
    html_list = [generate_row_html(fill_cols(vote)) for vote in votes[0:middle]]
    html = "".join(html_list)
    tables[0]['html'] = html
    tables[0]['class'] = 'vote_list_left'

    html_list = [generate_row_html(fill_cols(vote)) for vote in votes[middle:]]
    html = "".join(html_list)
    tables[1]['html'] = html
    tables[1]['class'] = 'vote_list_right'

    user_votes = {'up': UserVote.objects.get_count(session, 1),
                  'down': UserVote.objects.get_count(session, -1)}

    args = {'vote_list': votes, 'tables': tables, 'score_table': score_table,
            'tags': Tag.objects.get_for_object(session), 'switch_district': True,
            'user_votes': user_votes}

    return args

def show_session(request, plsess, sess, section=None):
    try:
        number = int(sess)
    except ValueError:
        raise Http404

    psess = get_object_or_404(PlenarySession, url_name=plsess)
    session = get_object_or_404(Session, plenary_session=psess, number=number)

    if not section:
        section = 'basic'
    if section == 'basic':
        args = show_session_basic(request, session, psess)
    elif section == 'comments':
        args = {'next': request.path}
    else:
        raise Http404

    args['psession'] = psess
    args['session'] = session
    args['active_page'] = 'sessions'
    args['section'] = section

    return render_to_response('show_session.html', args, context_instance=RequestContext(request))

@csrf_exempt
@postonly
def set_session_user_vote(request, plsess, sess):
    if not request.user.is_authenticated():
        raise Http403()
    try:
        number = int(sess)
    except ValueError:
        raise Http404
    sess = get_object_or_404(Session, plenary_session__url_name=plsess,
                             number=number)

    return set_user_vote(request, sess)

@login_required
def tag_session(request, plsess, sess):
    psess = get_object_or_404(PlenarySession, url_name=plsess)
    try:
        number = int(sess)
    except ValueError:
        raise Http404
    sess = get_object_or_404(Session, plenary_session=psess, number=number)

    if request.method != 'POST' or not 'tag' in request.POST:
        return HttpResponseBadRequest()

    tag = request.POST['tag']
    if not tag.isalnum():
        return HttpResponseBadRequest()
    Tag.objects.add_tag(sess, tag)

    kwargs = { 'plsess': plsess, 'sess': str(number) }
    path = reverse('votes.views.show_session', kwargs=kwargs)
    return HttpResponseRedirect(path)

def format_stat_col(request, val, class_name, is_percent=True):
    if val:
        if is_percent:
            s = "%.0f %%" % (val * 100.0)
            s2 = "%.02f %%" % (val * 100.0)
        else:
            s = ""
            while val > 1000:
                s = " %03d%s" % (val % 1000, s)
                val = val / 1000
            s = "%d%s" % (val, s)
            s2 = s
        col = { 'value': s, 'title': s2 }
    else:
        col = { 'value': '' }
    if class_name:
        col['class'] = class_name
    return col

def list_members(request):
    (date_begin, date_end) = find_period(request)
    district = find_district(request, date_begin, date_end)
    if district:
        query = Member.objects.in_district(district, date_begin, date_end)
    else:
        query = Member.objects.active_in(date_begin, date_end)

    sort_key = request.GET.get('sort')
    if sort_key and sort_key[0] == '-':
        sort_key = sort_key[1:]
        sort_reverse = True
    else:
        sort_reverse = False
    if sort_key not in ['name', 'party', 'att', 'pagree', 'sagree', 'st_cnt', 'el_bud']:
        sort_key = 'name'
    calc_keys = ['att', 'pagree', 'sagree', 'st_cnt', 'el_bud']
    if sort_key in calc_keys:
        stat_attr = ['attendance', 'party_agree', 'session_agree', 'statement_count',
                     'election_budget']
        stat_attr = stat_attr[calc_keys.index(sort_key)]
        # Some fields are calculated dynamically, so we need
        # to calculate it for all objects first in order to
        # sort to work.
        members = list(query.order_by('name'))
        for mem in members:
            mem.stats = mem.get_stats(date_begin, date_end)
            if not mem.stats:
                mem.sort_key = float(0)
            else:
                mem.sort_key = getattr(mem.stats, stat_attr)
        members.sort(key=operator.attrgetter('sort_key'), reverse=sort_reverse)
    else:
        if sort_reverse:
            sort_key = '-' + sort_key
        members = query.select_related('party').order_by(sort_key, 'name')

    paginator = Paginator(members, 15)
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
    try:
        member_page = paginator.page(page)
    except (EmptyPage, InvalidPage):
        member_page = paginator.page(paginator.num_pages)

    hdr_cols = []
    hdr_cols.append({ 'name': _('Party'), 'sort_key': 'party' })
    hdr_cols.append({ 'name': '' })
    hdr_cols.append({ 'name': _('Name'), 'sort_key': 'name', 'class': 'member_list_name' })

    hdr_cols.append({ 'name': _('ATT'), 'sort_key': 'att', 'class': 'member_list_stat',
        'title': _('Attendance in voting sessions'), 'img': 'images/icons/attendance.png', 'no_tn': True})
    hdr_cols.append({ 'name': _('PA'), 'sort_key': 'pagree', 'class': 'member_list_stat',
        'title': _('Agreement with party majority'), 'img': 'images/icons/party_agr.png', 'no_tn': True})
    hdr_cols.append({ 'name': _('SA'), 'sort_key': 'sagree', 'class': 'member_list_stat',
        'title': _('Agreement with session majority'), 'img': 'images/icons/session_agr.png', 'no_tn': True})
    hdr_cols.append({ 'name': _('St'), 'sort_key': 'st_cnt', 'class': 'member_list_stat',
        'title': _('Number of statements'), 'img': 'images/icons/nr_statements.png', 'no_tn': True})
    hdr_cols.append({ 'name': _('ElBud'), 'sort_key': 'el_bud', 'class': 'member_list_stat',
        'title': _('Election budget'), 'img': 'images/icons/election_budget.png', 'no_tn': True})
    for col in hdr_cols:
        if 'img' in col:
            col['img_alt'] = col['title']
        if not 'sort_key' in col:
            continue
        if sort_key == col['sort_key'] and not sort_reverse:
            val = '-' + col['sort_key']
        else:
            val = col['sort_key']
        col['link'] = generate_modified_query(request, 'sort', val, remove=['page'])
    hdr_html = generate_header_html({'cols': hdr_cols, 'id': 'member_list_head'})

    row_list = []
    for mem in member_page.object_list:
        col_vals = []
        if mem.party:
            col_vals.append({'img': mem.party.logo, 'img_alt': 'logo', 'img_dim': '36x36',
                    'title': mem.party.full_name, 'class': 'member_list_party' })
        else:
            col_vals.append(None)
        col_vals.append({'img': mem.photo, 'img_alt': 'portrait', 'link': mem.url_name,
                         'img_dim': '28x42', 'class': 'member_list_portrait'})
        col_vals.append({'value': mem.name, 'link': mem.url_name, 'class': 'member_list_name'})

        if not hasattr(mem, 'stats'):
            mem.stats = mem.get_stats(date_begin, date_end)
        CLASS_NAME = 'member_list_stat'
        if mem.stats:
            col_vals.append(format_stat_col(request, mem.stats.attendance, CLASS_NAME))
            col_vals.append(format_stat_col(request, mem.stats.party_agree, CLASS_NAME))
            col_vals.append(format_stat_col(request, mem.stats.session_agree, CLASS_NAME))
            col_vals.append({'value': str(mem.stats.statement_count), 'class': CLASS_NAME + ' member_list_statements'})
            col_vals.append(format_stat_col(request, mem.stats.election_budget, CLASS_NAME, is_percent=False))
        else:
            col_vals.append(None)
            col_vals.append(None)
            col_vals.append(None)
            col_vals.append(None)
            col_vals.append(None)
        row_list.append(generate_row_html(col_vals))
    table_html = "".join(row_list)

    return render_to_response('members.html',
                             {'member_page': member_page, 'switch_term': True,
                              'switch_district': True, 'switch_county': True,
                              'hdr': hdr_html,
                              'rows': table_html, 'active_page': 'members'},
                              context_instance = RequestContext(request))

def generate_member_stat_table(request, member, stats):
    table = {}

    hdr = []
    hdr.append({ 'name': _('Term'), 'class': 'member_list_name' })
    hdr.append({ 'name': _('ATT'), 'sort_key': 'att', 'class': 'member_list_stat',
        'title': _('Attendance in voting sessions'), 'img': 'images/icons/attendance.png', 'no_tn': True})
    hdr.append({ 'name': _('PA'), 'sort_key': 'pagree', 'class': 'member_list_stat',
        'title': _('Agreement with party majority'), 'img': 'images/icons/party_agr.png', 'no_tn': True})
    hdr.append({ 'name': _('SA'), 'sort_key': 'sagree', 'class': 'member_list_stat',
        'title': _('Agreement with session majority'), 'img': 'images/icons/session_agr.png', 'no_tn': True})
    hdr.append({ 'name': _('St'), 'sort_key': 'st_cnt', 'class': 'member_list_stat',
        'title': _('Number of statements'), 'img': 'images/icons/nr_statements.png', 'no_tn': True})
    hdr.append({ 'name': _('ElBud'), 'sort_key': 'el_bud', 'class': 'member_list_stat',
        'title': _('Election budget'), 'img': 'images/icons/election_budget.png', 'no_tn': True})
    table['header'] = hdr

    vals = []
    CLASS_NAME = 'member_list_stat'
    for s in stats:
        row = []
        name = None
        for term in term_list:
            if str(term.begin) != str(s.begin):
                continue
            if (not term.end and not s.end) or str(term.end) == str(s.end):
                name = term.display_name
                break
        if not name:
            name = str(s.begin) + PERIOD_DASH
            if s.end:
                name += str(s.end)
        row.append({ 'value': name })
        s.calc()
        row.append(format_stat_col(request, s.attendance, CLASS_NAME))
        row.append(format_stat_col(request, s.party_agree, CLASS_NAME))
        row.append(format_stat_col(request, s.session_agree, CLASS_NAME))
        row.append({ 'value': str(s.statement_count), 'class': CLASS_NAME })
        row.append(format_stat_col(request, s.election_budget, CLASS_NAME, is_percent=False))
        if not s.attendance and not s.statement_count:
            continue;
        vals.append(row)
    table['body'] = vals
    return table


def show_member_votes(request, member):
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
    sort_key = request.GET.get('sort')
    if sort_key and sort_key[0] == '-':
        sort_key = sort_key[1:]
        sort_reverse = True
    else:
        sort_reverse = False
    if sort_key not in ('session', 'vote'):
        sort_key = 'session'
        sort_reverse = not sort_reverse
    if sort_key == 'vote':
        order = 'vote'
        sort_reverse = not sort_reverse
    elif sort_key == 'session':
        order = 'session__plenary_session__date'
    if sort_reverse:
        order = '-' + order
    query = Q(member = member)
    query &= Q(vote__in=['Y', 'N', 'E'])
    vote_list = Vote.objects.filter(query).order_by(order, '-session__number')
    if vote_list.count():
        paginator = Paginator(vote_list, 30)
        try:
            vote_page = paginator.page(page)
        except (EmptyPage, InvalidPage):
            vote_page = paginator.page(paginator.num_pages)
    else:
        vote_page = None

    return {'vote_page': vote_page}

def show_member_basic(request, member):
    pa_list = PartyAssociation.objects.filter(member=member).order_by('begin')
    pa_list = pa_list.select_related('party__full_name')
    da_list = DistrictAssociation.objects.filter(member=member).order_by('begin')
    member.pa_list = pa_list
    member.da_list = da_list

    stats = MemberStats.objects.filter(member = member)
    stat_list = []
    for term in term_list:
        for st in stats:
            if (str(st.begin) == str(term.begin)) and (str(st.end) == str(term.end)):
                stat_list.append(st)
                break
    if stat_list:
        table = generate_member_stat_table(request, member, stat_list)
    else:
        table = None

    user_votes = {'up': UserVote.objects.get_count(member, 1),
                  'down': UserVote.objects.get_count(member, -1)}

    return {'stats_table': table, 'user_votes': user_votes }

def show_member_statements(request, member):
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    statements = Statement.objects.filter(member = member)
    statements = statements.order_by('-plenary_session__date', 'dsc_number', 'index')
    paginator = Paginator(statements, 10)
    try:
        statement_page = paginator.page(page)
    except (EmptyPage, InvalidPage):
        statement_page = paginator.page(paginator.num_pages)

    return {'statement_page': statement_page}

def show_member_opinions(request, member):
    answers = Answer.objects.filter(member=member)
    ret = {'answers': answers}
    return ret

def show_member(request, member, section=None):
    member = get_object_or_404(Member, url_name=member)
    if not section:
        section = 'basic'
    if section == 'basic':
        args = show_member_basic(request, member)
    elif section == 'votes':
        args = show_member_votes(request, member)
    elif section == 'comments':
        args = {'next': request.path}
    elif section == 'statements':
        args = show_member_statements(request, member)
    elif section == 'opinions':
        args = show_member_opinions(request, member)
    else:
        raise Http404

    args['member'] = member
    args['section'] = section
    args['active_page'] = 'members'

    return render_to_response('show_member.html', args, context_instance=RequestContext(request))

@csrf_exempt
@postonly
def set_member_user_vote(request, member):
    if not request.user.is_authenticated():
        raise Http403()
    member = get_object_or_404(Member, url_name=member)

    return set_user_vote(request, member)

def show_plsession(request, plsess, section=None, dsc=None):
    psess = get_object_or_404(PlenarySession, url_name=plsess)
    if not 'section':
        section = 'basic'
    if section == 'basic':
        try:
            minutes = Minutes.objects.get(plenary_session=psess)
        except Minutes.DoesNotExist:
            minutes = None
        args = {'minutes': minutes}
    elif section == 'statements':
        try:
            dsc = int(dsc)
        except ValueError:
            raise Http404
        statements = Statement.objects.filter(plenary_session=psess,
                                              dsc_number=dsc)
        statements = list(statements.order_by('index'))
        if not statements:
            raise Http404
        args = {'st_list': statements}
    else:
        raise Http404
    args['psession'] = psess
    args['section'] = section
    args['active_page'] = 'sessions'
    return render_to_response('show_plsession.html', args,
                              context_instance=RequestContext(request))

def list_parties(request):
    party_list = get_list_or_404(Party)
    args = { 'party_list': party_list, 'active_page': 'parties' }
    return render_to_response('list_parties.html', args,
                              context_instance=RequestContext(request))

def get_req_param_int(request, param):
    try:
        val = int(request.GET.get(param, 0))
    except ValueError:
        val = 0
    return val

def val_in_range(val, limits):
    return val >= limits[0] and val <= limits[1]

def search_autocomplete(request):
    name = request.GET.get('name', '')
    max_results = get_req_param_int(request, 'max_results')
    if not val_in_range(max_results, (1, 100)):
        return HttpResponseBadRequest();
    thumbnail_width = get_req_param_int(request, 'thumbnail_width')
    thumbnail_height = get_req_param_int(request, 'thumbnail_height')
    # TODO: is this enough to defeat any DoS attempts?
    if not val_in_range(thumbnail_width, THUMBNAIL_WIDTH_LIMITS) or     \
            not val_in_range(thumbnail_height, THUMBNAIL_HEIGHT_LIMITS):
       return HttpResponseBadRequest();

    words = name.split()
    full_word_cnt = len(words)
    if full_word_cnt > 10:
        return HttpResponseBadRequest();
    if full_word_cnt == 0:
        member_query = Member.objects.all()[:max_results]
        keyword_query = Keyword.objects.all()[:max_results]
    else:
        member_q = Q()
        keyword_q = Q()

        trailing_space = name[-1] == ' '
        if not trailing_space:
            full_word_cnt -= 1

        for w in words[:full_word_cnt]:
            re = r'(^| )' + w + r'( |$)'
            member_q &= Q(name__iregex=re)
            keyword_q &= Q(keyword__iregex=re)
        if not trailing_space:
            re = r'(^| )' + words[-1]
            member_q &= Q(name__iregex=re)
            keyword_q &= Q(keyword__name__iregex=re)

        member_query = Member.objects.filter(member_q).            \
                                order_by("name")[:max_results]
        keyword_query = SessionKeyword.objects.filter(keyword_q).  \
                                order_by("keyword__name").         \
                                values("keyword__name").           \
                                distinct()[:max_results]

    result_list = []
    for x in member_query:
        tn = DjangoThumbnail(x.photo, (thumbnail_width, thumbnail_height))
        result_list.append((x.name, unicode(tn), "/search/?query=" + x.name))

    for x in keyword_query:
        if (len(result_list) == max_results):
            break
        result_list.append((x['keyword__name'], "",
                            "/search/keyword/?query=" + x['keyword__name']))

    result_list.sort(key=lambda n:n[0])

    json = simplejson.dumps(result_list)
    response = HttpResponse(json, mimetype="text/javascript")

    return response

def mp_hall_of_fame(max_results):
    thumbnail_width = 70
    thumbnail_height = 70

    memb_ctype_id = ContentType.objects.get_for_model(Member).id
    query = Member.objects.raw("""
        select *,count(score) as like_cnt
        from user_votes as v
        join votes_member m on v.object_id = m.id
        where v.content_type_id = %s and v.score > 0
        group by m.id
        order by like_cnt desc
    """, [memb_ctype_id])[:max_results]
    member_list=[]
    for memb in query:
        tn = DjangoThumbnail(memb.photo, (thumbnail_width, thumbnail_height))
        member_list.append({
            'name'      : memb.name,
            'url_name'  : memb.url_name,
            'thumbnail' : unicode(tn),
            'like_cnt'  : memb.like_cnt})

    return member_list

def search(request):
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    if 'query' not in request.GET:
        raise Http404
    query = request.GET['query']
    res = complete_indexer.search(query)
    res = res.flags(djapian.resultset.xapian.QueryParser.FLAG_WILDCARD)
    paginator = Paginator(res, 15)
    result_page = paginator.page(page)
    for hit in result_page.object_list:
        if type(hit.instance) == Member:
            hit.url = '/member/%s/' % (hit.instance.url_name)
            hit.underline = True
        elif type(hit.instance) == Session:
            s = hit.instance
            hit.url = '/session/' + s.plenary_session.url_name + '/' + str(s.number)
            hit.info = s.info
            s.info = s.info.replace('\n', '\n\n')
        elif type(hit.instance) == Statement:
            s = hit.instance
            hit.url = '/session/%s/statements/%d/#statement-%d' % (s.plenary_session.url_name, s.dsc_number, s.index)
            hit.info = s.text[0:200].replace('\n', '\n\n') + "..."

    return render_to_response('search.html', {'result_page': result_page},
                              context_instance = RequestContext(request))

def search_county(request):
    name = request.GET.get('name', '')
    try:
        max_results = int(request.GET.get('max_results', 0))
    except ValueError:
        max_results = 0
    if max_results <= 0:
        return HttpResponseBadRequest()

    name = name.rstrip()
    if name == '':
        county_list = County.objects.all()
    else:
        county_list = County.objects.filter(name__istartswith=name)

    county_list = county_list.order_by('name')[:max_results].   \
                              values_list('name', flat=True)
    county_list = [(x,) for x in county_list]

    json = simplejson.dumps(county_list)

    response = HttpResponse(json, mimetype="text/javascript")
    response['Cache-Control'] = "max-age=1000"
    response['Expires'] = http_date(time.time() + 1000)

    return response

def about(request, section):
    args = {'active_page': 'info', 'section': section}

    args['news'] = Newsitem.objects.newest()

    if section == 'main':
        args['content'] = Item.objects.retrieve_content('main')
        section_name = _('Home')
    elif section == 'background':
        args['content'] = Item.objects.retrieve_content('background')
        section_name = _('Background')
    elif section == 'contact':
        args['content'] = Item.objects.retrieve_content('contact')
        section_name = _('Contact')
    elif section == 'feedback':
        # Feedback does not contain anything long at the moment, left out of cms
	section_name = _('Feedback')
    else:
        raise Http404
    sess_list = Session.objects.all().order_by('-plenary_session__date', '-number')
    sess_list = sess_list.select_related('plenary_session')[:5]
    for ses in sess_list:
        ses.count_votes()
#        ses.info = ses.info.replace('\n', '\n\n')

    args['sess_list'] = sess_list
    args['section_name'] = section_name
    args['mp_hall_of_fame'] = mp_hall_of_fame(10)
    if section == 'feedback':
        return contact_form(request, template_name='main_page.html',
                            extra_context=args)
    return render_to_response('main_page.html', args,
                              context_instance=RequestContext(request))
