from django.shortcuts import render_to_response
from django.template import RequestContext
from kamu.cms.models import Item, Newsitem

def show_news(request):
    return render_to_response('press_release.html',
                              context_instance=RequestContext(request))

def render_news(request, date, index):
    date = date.replace('/', '-')
    item = Newsitem.objects.get(date=date)
    revision = item.get_latest()
    args = {'revision': revision, 'item': item}

    return render_to_response('full_news.html', args,
                              context_instance=RequestContext(request))
