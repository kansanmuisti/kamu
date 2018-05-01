import operator
from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import render_to_response, get_list_or_404, get_object_or_404
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.db.models import Q, Count
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe
from django.utils.http import urlencode
from sorl.thumbnail import get_thumbnail

from parliament.models import *
from parliament.api import *

TERM_KEY = 'term'
DISTRICT_KEY = 'district'
COUNTY_KEY = 'county'

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
        if county_name != 'All counties':
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

def generate_modified_query(request, mod_key, mod_val, remove=[]):
    params = dict(list(request.GET.items()))
    for k in remove:
        if k in params:
            del params[k]
    params[mod_key] = mod_val
    return request.path + '?%s' % urlencode(params)

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
            tn = get_thumbnail(val['img'], val['img_dim'])
            html += '<img src="%s" alt="%s" />' % (tn.url, val['img_alt'])
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
                img_src = str(img_src)
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
    pa_list = pa_list.select_related('party__name')
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

    user_votes = get_user_votes(request.user, member)

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
    answers = answers.select_related('option', 'option__question',
                            'option__question__source')

    congruences = VoteOptionCongruence.objects.get_vote_congruences(for_member=member, for_user=request.user)
    congruences = itertools.groupby(congruences, lambda c: c.option_id)
    # Somebody seems to read the iterator before we make it
    # a list later, can't be bothered to debug now
    congruences = ((g, list(c)) for (g, c) in congruences)
    congruences = dict(congruences)

    # itertools.groupby requires a sorted list :(
    a_with_cong = []
    rest = []
    for a in answers:
        a_congs = congruences.get(a.option_id, None)
        if a_congs is not None:
            a_congs = list(a_congs)
            a_cong_values = [c.congruence for c in a_congs]
            a.congruence = sum(a_cong_values)/len(a_cong_values)
            a.relevant_votes = a_congs
            a_with_cong.append(a)
        else:
            a.congruence = None
            a.relevant_votes = []
            rest.append(a)

    
    answers = list(itertools.chain(a_with_cong, rest))
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
