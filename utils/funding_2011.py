import re
from lxml import etree, html
import http_cache, parse_tools
from votes.models import Member, TermMember, Term, MemberStats

URL_BASE='http://www.puoluerahoitusvalvonta.fi/fi/index/vaalirahailmoituksia/ilmoituslistaus/EV2011/%02d.html'

TERM="2011-2014"
term = Term.objects.get(name=TERM)

mp_count = 0

def process_mp(mp, url):
    tm = TermMember.objects.filter(member=mp, term=term)
    if not tm:
        return
    s = http_cache.open_url(url, 'funding')
    doc = html.fromstring(s)

    election_budget = None

    rows = doc.xpath(".//tr")
    for row in rows:
        th = row.getchildren()[0]
        if not th.tag == 'th' or not th.text:
            continue
        if th.text.strip().startswith('2. Vaalikampanjan rahoitus'):
            scr = row[1][0]
            assert scr.tag == 'script'
            m = re.search(r"addSpaces\('([\d,.]*)'\)", scr.text)
            assert m
            s = m.groups()[0].replace(',', '.')
            if not s:
                continue
            election_budget = float(s)
    if not election_budget:
        return

    global mp_count
    mp_count += 1
    ms = MemberStats.objects.get(begin=term.begin, end=term.end, member=mp)
    ms.election_budget = election_budget
    ms.save()
    print "%30s: %.0f" % (mp.name, election_budget)

def process_district(district):
    url = URL_BASE % district
    s = http_cache.open_url(url, 'funding')
    doc = html.fromstring(s)
    doc.make_links_absolute(url)

    el_list = doc.xpath(".//div[@class='listing_table']")
    for el in el_list:
        rows = el.xpath(".//tr")
        for row in rows:
            ch = row.getchildren()[0]
            if ch.tag == 'th':
                continue
#            print ch.text
            m = re.match('([\w -]+)[ ]{2,}([\w -]+)', ch.text, re.U)
            if not m:
                print "Skipping %s" % ch.text
                continue
            fnames = m.groups()[0].strip()
            lname = m.groups()[1].strip()
            name = "%s %s" % (lname, fnames.split(' ')[0])
            name = parse_tools.fix_mp_name(name)

            mp = Member.objects.filter(name=name)
            if not mp:
                continue
            mp = mp[0]
            links = row.xpath('.//a')
            link = None
            for l in links:
                href = l.attrib['href']
                if l.text.strip() == "Ennakkoilmoitus":
                    if not link:
                        link = href
                elif l.text.strip() == "Vaalirahoitusilmoitus":
                    link = href
                else:
                    assert False
            assert link
            process_mp(mp, link)

def parse():
    for district in range(1, 16):
        process_district(district)
    print "Funding data found for %d MPs" % mp_count
