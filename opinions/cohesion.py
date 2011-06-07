import numpy as np
import functools
import itertools

if __name__ == '__main__':
	import sys
	import os
	sys.path.append(os.path.abspath(__file__ + '/../..'))
	from django.core.management import setup_environ
	import settings
	setup_environ(settings)

from opinions.models import Answer, Option, Question, QuestionSource
from votes.models import TermMember, Term, Member, Party

from django.db.models import Count

YLE_LIKERT_MAP = {
	u't\xe4ysin samaa mielt\xe4': 1,
	u'jokseenkin samaa mielt\xe4': 0.5,
	u'jokseenkin eri mielt\xe4': -0.5,
	u't\xe4ysin eri mielt\xe4': -1,
	u'en osaa sanoa': 0
	}

def option_likert_value(option):
	if not option: return None
	if option.question.source.url_name != 'yle2011':
		return None
	
	return YLE_LIKERT_MAP.get(option.name, None)
	

def answers_to_recarray(answers):
	records = []
	for a in answers:
		value = option_likert_value(a.option)
		if value is None: continue
		records.append((a.question_id, value, a.member_id, a.member.party_id))
	
	return np.rec.fromrecords(records, names='question,value,member,party')

def rec_groupby(rec, field):
	for v in np.unique(rec[field]):
		yield v, rec[rec[field] == v]

def binary_consensus_vote(a):
	a = a[a != 0]
	winner = 1 if np.sum(a > 0) > np.sum(a < 0) else -1
	return winner

def binary_question_cohesion(a, winner=None):
	"""
	Calculate the binary cohesion of the answers
	
	If (not winner), the winner is calculated
	from the answers

	Cohesion is the share of answers that agree with
	a decided answer. The decided answer is (usually)
	the majority of all answers (of the coalition).
	The strength of the answer is ignored.

	In the usual case the cohesion described as:

	Cohesion is the share of answers that
	agree with the majority answer of the cabinet.
	"""
	a = a[a != 0]
	winner = winner or binary_consensus_vote(a)
	lies = np.sum(np.sign(a) != winner)
	return (lies, np.sum(a != 0))


def aggregated_binary_cohesion(lies, answers):
	lie_share = np.sum(lies)/float(np.sum(answers))
	return 1.0-lie_share


def cabinet_party_binary_question_cohesions(answers, cabinet=None):
	if cabinet:
		answers = answers[np_in(answers['party'], cabinet)]
	else:
		cabinet = np.unique(answers['party'])

	records = []
	for q, a in rec_groupby(answers, 'question'):
		winner = binary_consensus_vote(a['value'])
		for p, a in rec_groupby(a, 'party'):
			cohesion_stats = binary_question_cohesion(a['value'], winner)
			records.append(tuple([q, p]+list(cohesion_stats)))

	return np.rec.fromrecords(records, names='question,party,lies,answers')


def groupby(lst, grouping, sorting = None):
	sorting = sorting or grouping
	lst = sorted(lst, key=sorting)
	return itertools.groupby(lst, grouping)

def np_in(a, choices):
	return reduce(lambda t,c: t | (a == c), choices, np.zeros(len(a), dtype=bool))

def get_cabinet_combinations(parties):
	possibilities = (itertools.combinations(parties, n)
			for n in range(1, len(parties)+1))
	possibilities = itertools.chain(*possibilities)
	return possibilities

def cabinet_size(party_sizes, cabinet):
	return sum(party_sizes[p] for p in cabinet)

def get_majority_cabinets(party_sizes):
	cab_size = functools.partial(cabinet_size, party_sizes)
	total_members = sum(party_sizes.itervalues())
	possibilities = get_cabinet_combinations(party_sizes.keys())
	possibilities = (c for c in possibilities if cab_size(c) > total_members/2)
	return possibilities

def get_party_sizes(term):
	member_terms = TermMember.objects.filter(term=term)
	party_sizes = member_terms.values('member__party').annotate(Count('member__party'))
	party_sizes = dict((s['member__party'], s['member__party__count'])
				for s in party_sizes)
	return party_sizes

class CabinetStats:
	def __init__(self, cabinet, stats, all_answers):
		self.cabinet = cabinet
		self.stats = stats
		self.all_answers = all_answers
	
	def cohesion(self, party=None, question=None):
		stats = self.stats
		if party: stats = stats[stats['party'] == party]
		if question is not None: stats = stats[stats['question'] == question]

		return aggregated_binary_cohesion(stats['lies'], stats['answers'])

	@property
	def questions(self):
		return map(int, np.unique(self.stats['question']))
	
	def answers(self, question=None):
		my_answers = np_in(self.all_answers['party'], self.cabinet)
		answers = self.all_answers[my_answers]
		if question is not None:
			answers = answers[answers['question'] == question]
		return answers
	
	def cabinet_answer(self, question):
		# TODO: Cache if this causes performance problems
		return binary_consensus_vote(self.answers(question)['value'])
	

class AllCabinetStats(dict):
	def _immutable(self, *args, **kwargs):
		raise AttributeError("Can't add/change values in AllCabinetStats")
	__setitem__ = update = _immutable
	

	def __init__(self, stats, party_sizes, answers):
		stats = ((tuple(sorted(key)), value)
				for key, value in stats.iteritems())
		dict.__init__(self, stats)
		self.party_sizes = party_sizes
		self.answers = answers

		self.cohesion_cache = {}

	def __getitem__(self, item):
		return dict.__getitem__(self, tuple(sorted(item)))

	def __call__(self, cabinet, questions=None):
		stats = self[cabinet]
		if questions:
			stats = stats[np_in(stats['question'], questions)]

		return CabinetStats(cabinet, stats, self.answers)
	
	@property
	def questions(self):
		return self(self.iterkeys().next()).questions

	def all_cohesions(self, questions=None):
		if questions:
			key = tuple(sorted(questions))
		else:
			key = None
		
		if key in self.cohesion_cache:
			cohesions = self.cohesion_cache[key]
			return cohesions
		
    		cab_cohesion = lambda c: self(c, questions).cohesion()
    		cab_size = lambda c: cabinet_size(self.party_sizes, c)
		cabinet_cohesions = [(cab_cohesion(c), c, cab_size(c))
       					for c in self.iterkeys()]
		cabinet_cohesions.sort(key=lambda (coh, cab, size): (coh, -size))
		self.cohesion_cache[key] = cabinet_cohesions
		
		return cabinet_cohesions

	def majority_cohesions(self, questions=None):
		total_members = sum(self.party_sizes.itervalues())
		cohesions = self.all_cohesions(questions)
		cohesions = [c for c in cohesions if c[2] > total_members/2]
		return cohesions


def get_all_cabinet_statistics(questions, term):
	member_terms = TermMember.objects.filter(term=term)
	answers = Answer.objects.filter(question__in=questions, member__in=member_terms.values('member'))
	answers = answers.select_related('option', 'option__question',
					'option__question__source', 'member')
	answers = answers_to_recarray(answers)
	
	party_sizes = get_party_sizes(term)
	
	data = {}
	for cabinet in get_cabinet_combinations(party_sizes.keys()):
		stats = cabinet_party_binary_question_cohesions(answers, cabinet)
		data[cabinet] = stats
	
	all_stats = AllCabinetStats(data, party_sizes, answers)

	return all_stats

def cached_all_cabinet_statistics(*args):
	import cPickle
	cachepath = '/tmp/cabinet_cohesions.pickle'
	try:
		return cPickle.load(open(cachepath))
	except:
		pass

	stats = get_all_cabinet_statistics(*args)
	cPickle.dump(stats, open(cachepath, 'w'))
	return stats

def test():
	term = Term.objects.get(name='2011-2014')
	questions = QuestionSource.objects.get(url_name='yle2011').question_set.all()
	stats = cached_all_cabinet_statistics(questions, term)
	#print len(map(stats.total_cohesion, stats.keys()))
	print stats.majority_cohesions()
	print stats.majority_cohesions()
	print_rows = []
	for cabinet in stats.keys():
		questions = (100, 101)
		cabstats = stats(cabinet, questions)
		row = "%.1f\n"%(cabstats.cohesion()*100)
		row += reduce(lambda s, p: s+"%s\t"%(p), cabinet, '')+"\n"
		row += reduce(lambda s, p: s+"%.1f\t"%(cabstats.cohesion(party=p)*100), cabinet, '')+"\n"
		print_rows.append((cabstats.cohesion(), row))

	for c, row in sorted(print_rows, reverse=True):
		print row
	

if __name__ == '__main__':
	test()
