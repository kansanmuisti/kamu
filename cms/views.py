from django.shortcuts import render_to_response
from django.template import RequestContext

def show_news(request):
    return render_to_response('press_release.html',
                              context_instance=RequestContext(request))
