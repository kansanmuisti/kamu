from parliament.models import *

types = MemberActivityType.objects.all()
st_count = 0
start_date = '2014-02-06'
start_date = '2011-04-20'
for t in types:
    act_qs = MemberActivity.objects.filter(type=t, time__gte=start_date)
    act_count = act_qs.count()
    mp_count = Member.objects.filter(memberactivity__in=act_qs).distinct().count()
    print(("%s: %d %d" % (t.type, act_count, mp_count)))
    if mp_count:
        t.count = act_count / (1.0 * mp_count)
    else:
        t.count = 0
    if t.type == 'ST':
        st_count = t.count


for t in types:
    if not t.count:
        continue
    print(("%s: %f" % (t.type, st_count * 1.0 / t.count)))

