from django.shortcuts import render_to_response, get_list_or_404, get_object_or_404
from django.template import RequestContext
from kamu.opinions.models import *
from kamu.votes.models import Party

def list_questions(request):
	questions = Question.objects.all()
	parties = Party.objects.all()

	args = dict(questions=questions, parties=parties)
	return render_to_response('list_questions.html', args,
		context_instance=RequestContext(request))

def list_questions_static(request):
	return render_to_response('list_questions_static.html', {},
		context_instance=RequestContext(request))
