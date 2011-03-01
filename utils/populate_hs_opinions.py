import sys
import csv
import os

sys.path.append(os.path.abspath(__file__ + '/../../..'))
sys.path.append(os.path.abspath(__file__ + '/../..'))
from django.core.management import setup_environ
from kamu import settings
setup_environ(settings)

from kamu.opinions.models import *
from kamu.votes.models import Member

def get_reader(input):
	return csv.DictReader(input, delimiter=';', quotechar='"')

def parse_model(input, idcol):
	reader = get_reader(input)
	model = {}
	for row in reader:
		model[row[idcol]] = row
	return model

def parse_question_model(questions):
	return parse_model(questions, 'Question_id')

def parse_candidate_model(members):
	return parse_model(members, 'Candidate_id')

def parse_option_model(members):
	return parse_model(members, 'AnswerAlternative_id')

def populate_answers(answers, question_mapping, option_mapping, candidate_mapping):
	reader = get_reader(answers)
	for answer in reader:
		cid = answer['user_id']
		if(cid not in candidate_mapping):
			continue
		member = candidate_mapping[cid]
		option_id = answer['Answer_alternative_id']
		if(option_id == '0'):
			option = None
		else:
			option = option_mapping[option_id]
		
		Answer.objects.get_or_create(
			option=option,
			question=question_mapping[answer['Question_id']],
			member=member,
			explanation=answer['Explanation'])

def initialize_schema(questions, options, srcname, srcyear):
	src, c = QuestionSource.objects.get_or_create(name=srcname, year=srcyear)
	
	question_mapping = {}
	for id, question in questions.items():
		qm, c = Question.objects.get_or_create(
				text=question['Question'],
				source=src)
		question_mapping[id] = qm
	
	option_mapping = {}
	for id, option in options.items():
		om, c = Option.objects.get_or_create(
				question=question_mapping[option['Question_id']],
				name=option['Answer_text'],
				weight=option['AnswerAlternative_number'])
		option_mapping[id] = om
	
	return (question_mapping, option_mapping)

def get_candidate_mapping(candidates):
	reader = get_reader(candidates)
	mapping = {}
	for member in reader:
		fullname = ' '.join((member['Last_name'], member['First_name']))
		matches = Member.objects.filter(name=fullname)
		
		if(matches.count() == 0):
			#print >>sys.stderr, "No match for %s"%fullname
			continue
		elif(matches.count() > 1):
			print matches
			print >>sys.stderr, "Ambiguous match for %s"%fullname
			continue

		mapping[member['Candidate_id']] = matches[0]
	print >>sys.stderr, "%i members accepted"%len(mapping)
	return mapping

def populate_database(questions, options, candidates, answers):
	candidate_mapping = get_candidate_mapping(open(candidates, 'r'))

	qm = parse_question_model(open(questions, 'r'))
	om = parse_option_model(open(options, 'r'))

	question_map, option_map = initialize_schema(qm, om, 'HS vaalikone', 2007)
	cm = parse_candidate_model(open(candidates, 'r'))
	
	populate_answers(open(answers, 'r'), question_map,
		option_map , candidate_mapping)


if(__name__ == '__main__'):
	populate_database(*sys.argv[1:])
	
