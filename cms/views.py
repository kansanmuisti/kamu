from django.shortcuts import render_to_response, redirect
from django.contrib.auth.decorators import login_required
from httpstatus.decorators import postonly
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseServerError, HttpResponseBadRequest
from httpstatus import Http403
from kamu.cms.models import Category, Item, Newsitem, Revision, Content
from kamu.cms.models import NewRevisionForm
from django.utils.safestring import mark_safe
from django.utils.translation import get_language
from datetime import date

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

@login_required
def add_newsitem(request):
    if not request.user.is_staff:
        raise Http403
    
    category = Category.objects.get(name='news')
    item = Newsitem(category=category, date=date.today())
    item.save()

    return edit_item(request, item.id)
    
@login_required
def edit_item(request, item_id):
    if not request.user.is_staff:
        raise Http403

    item = Item.objects.get(pk=item_id)
    revision = item.get_latest(lang=get_language())

    if request.method == 'POST':
        form = NewRevisionForm(request.POST, instance=revision)
        args = {'form': form, 'item': item }
        if form.is_valid():
            # We want to save a new one
            form.instance.id = None
            # For now just assume that missing revision == missing content
            if revision is None:
                content = Content(item=item, language=get_language())
                content.save()
                revision = form.save(commit=False)
                revision.content = content
                revision.save()
            else:
                form.save()
            # First iteration, at least news are shown on main page
            return redirect('/');
    else:
        form = NewRevisionForm(instance=revision)
        args = {'revision': revision, 'item': item, 'form': form}

    return render_to_response('edit_item.html', args,
                              context_instance=RequestContext(request))

@postonly
def preview_markdown(request):
    try:
        markdown_data = request.POST['renderable']
    except (KeyError):
        return HttpResponseBadRequest()

    try:
        import markdown

        md = markdown.Markdown()
        html = md.convert(markdown_data)

        args = {'section': 'background',
                'content': {'data': mark_safe(html)}}

        return render_to_response('main_page.html', args,
                                  context_instance=RequestContext(request))
    except ImportError:
        return HttpResponseServerError
