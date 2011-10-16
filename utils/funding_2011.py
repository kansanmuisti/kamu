import csv
import http_cache, parse_tools
from votes.models import Member, TermMember, Term, MemberStats

TERM="2011-2014"
term = Term.objects.get(name=TERM)

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

def parse(input_file):
    mp_list = Member.objects.active_in_term(term)
    mp_dict = {}
    for mp in mp_list:
        mp_dict[mp.name] = mp
        mp.found = False
    f = open(input_file, 'r')
    reader = csv.reader(f, delimiter=';', quotechar="'")
    reader.next() # skip header
    for row in reader:
        first_names = row[0].strip(" '").decode('utf8').split(' ')
        last_name = row[1].strip(" '").decode('utf8')
        last_name = unicode(last_name).replace(u'&eacute;', u'\u00e9')
        name = '%s %s' % (last_name, first_names[0])
        name = parse_tools.fix_mp_name(name)
        try:
            member = mp_dict[name]
        except KeyError:
#            print "MP '%s' not found" % name
            continue
        member.found = True
        funding = float(row[6].replace(',', '.'))
        print "%30s: %.2f" % (unicode(member), funding)
        ms = MemberStats.objects.get(begin=term.begin, end=term.end, member=member)
        ms.election_budget = funding
        ms.save()
#        print unicode(member)
    for mp in mp_list:
        if mp.found:
            continue
        print "Funding data for MP '%s' not found" % unicode(mp)

        """budget = row[4].strip().replace(',', '')
        name = "%s %s" % (last_name, first_name)
        name = parse_tools.fix_mp_name(name)
        print "%-20s %-20s %10s" % (first_name, last_name, budget)
        try:
            member = Member.objects.get(name=name)
            tm = TermMember.objects.get(member=member, term=term)
        except Member.DoesNotExist:
            continue
        except TermMember.DoesNotExist:
            continue
        ms = MemberStats.objects.get(begin=term.begin, end=term.end, member=member)
        tm.election_budget = budget
        tm.save()
        ms.election_budget = budget
        ms.save()"""
    f.close()


