import csv
from parliament.models import *

reader = csv.DictReader(open('hs-vastaukset.csv', 'r'), delimiter=';')
cand_dict = {}
for row in reader:
    cand_dict[row['name'].decode('utf8')] = row

writer = csv.DictWriter(open('new-mp-feeds.csv', 'w'), ['mp', 'type', 'feed'])
writer.writeheader()

mp_list = Member.objects.active_in_term(Term.objects.latest())
no_match = 0
for mp in mp_list:
    name = mp.get_print_name()
    if name not in cand_dict:
        no_match += 1
        continue
    feeds = {f.type: f for f in mp.membersocialfeed_set.all()}
    cand = cand_dict[name]
    if cand['twitter'] and cand['twitter'] != 'NULL' and 'TW' not in feeds:
        print('%s: TW: %s' % (mp.get_print_name(), cand['twitter']))
        writer.writerow({'mp': mp.name.encode('utf8'), 'type': 'TW', 'feed': cand['twitter']})
    if cand['facebook'] and cand['facebook'] != 'NULL' and 'FB' not in feeds:
        print('%s: FB: %s' % (mp.get_print_name(), cand['facebook']))
        writer.writerow({'mp': mp.name.encode('utf8'), 'type': 'FB', 'feed': cand['facebook']})
