import csv

from votes.models import Member, TermMember, Term, MemberStats

from . import parse_tools

TERM="2007-2010"

def parse(input_file):
    term = Term.objects.get(name=TERM)

    f = open(input_file, 'r')
    reader = csv.reader(f, delimiter=',', quotechar='"')
    for row in reader:
        first_name = row[1].strip()
        last_name = row[0].strip()
        budget = row[4].strip().replace(',', '')
        name = "%s %s" % (last_name, first_name)
        name = parse_tools.fix_mp_name(name)
        print("%-20s %-20s %10s" % (first_name, last_name, budget))
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
        ms.save()

    f.close()
