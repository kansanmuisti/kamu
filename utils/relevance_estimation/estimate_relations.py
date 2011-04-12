#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import division

import sys
import csv
import os
import itertools
import math
import shelve

sys.path.append(os.path.abspath(__file__ + '/../../../..'))
sys.path.append(os.path.abspath(__file__ + '/../../..'))
from django.core.management import setup_environ
from kamu import settings
setup_environ(settings)

from kamu.opinions.models import Question, QuestionSessionRelevance
from kamu.votes.models import Session

from lexicon import Lexicon, string_to_words

import ctypes

class BaseForms(object):

    def __init__(self):
        self.libc = ctypes.CDLL(None)
        self.lib = ctypes.CDLL('libmalaga.so')
        self.lib.init_libmalaga('sukija/suomi.pro')

    def __call__(self, word):
        return self.__convert(word)

    def __convert(self, word):
        self.lib.analyse_item(word.encode('utf-8'), 0)
        result = self.lib.first_analysis_result()
        ret = []
        while result:
            if self.lib.get_value_type(result) != 4:
                assert True, 'Unknown libmalaga result type!'
            s = ctypes.c_char_p(self.lib.get_value_string(result))
            ret.append(unicode(s.value, 'utf-8'))
            self.libc.free(s)
            result = self.lib.next_analysis_result()
        ret = list(set(ret))
        return ret

    def close(self):
        self.lib.terminate_libmalaga()

base_forms = BaseForms()

import libvoikko

class CompoundSplitter(object):

    def __init__(self):
        self.v = libvoikko.Voikko('fi')

    def __call__(self, word):
        words = []
        for analysis in self.v.analyze(word):
            structure = analysis['STRUCTURE'].split('=')[1:]
            if len(structure) < 2:
                continue
            i = 0
            for part in structure:
                wordpart = word[i:][:len(part)]
                wordpart = wordpart.strip('-')
                words.append(wordpart)

                i += len(part)
        return words

split_compound_word = CompoundSplitter()


def text_to_basewords(s):
    words = string_to_words(s)
    words = list(itertools.chain(*map(base_forms, words)))
    return words


def text_to_word_features(s):
    words = text_to_basewords(s)
    words.extend(itertools.chain(*map(split_compound_word, words)))
    return words


def lexicon_magnitude(l, full):
    mag = 0
    for (w, freq) in l.items():
        mag += (freq / full.data[w]) ** 2
    return math.sqrt(mag)


def lexicon_distance(a, b, full):
    common_words = set(a.data.keys()) & set(b.data.keys())
    dot = 0
    for w in common_words:
        dot += a.data[w] * b.data[w] / full.data[w] ** 2
    lengths = lexicon_magnitude(a, full) * lexicon_magnitude(b, full)
    if lengths == 0:
        return math.acos(0)

    return math.acos(dot / lengths)


def lexicon_relevance(a, b, full):
    distance = lexicon_distance(a, b, full)
    return 1 - distance / math.pi


def estimate_relations(cache_file='word_cache.shelve', docs=None):
    cache = shelve.open(cache_file)
    try:
        _estimate_relations(cache, docs)
    finally:
        cache.close()

def get_session_word_features_full(session, document_store, cache=None):
    documents = session.sessiondocument_set.filter(name__startswith='HE')
    words = []
    for document in documents:
        name = str(document.name)
        if name not in document_store:
            continue

        if name not in cache:
            doc = document_store[name]
            doc = unicode(doc, 'iso8859-1')
            docwords = text_to_word_features(doc)
            cache[name] = u' '.join(docwords)
        else:
            docwords = cache[name].split(' ')
        
        words.extend(docwords)

    return words

def get_session_word_features(session, cache=None, document_store=None):
    if(document_store is not None):
        return get_session_word_features_full(session, document_store, cache)
    documents = session.sessiondocument_set.filter(name__startswith='HE')
    words = []
    for document in documents:
        name = str(document.name)

        if name not in cache:
            doc = document.summary
            if(doc is None): continue
            #doc = unicode(doc, 'iso8859-1')
            docwords = text_to_word_features(doc)
            cache[name] = u' '.join(docwords)
        else:
            docwords = cache[name].split(' ')
        
        words.extend(docwords)

    return words



def _estimate_relations(cache, docs=None):
    lexicon = Lexicon()

    questions = {}
    question_objects = Question.objects.all()
    n_questions = question_objects.count()
    for (i, question) in enumerate(question_objects):
        print >>sys.stderr, "Handling question %i/%i"%(i+1, n_questions)
        name = 'question_%i' % question.id

        if name not in cache:
            words = text_to_word_features(question.text)

            for option in question.option_set.all():
                words.extend(text_to_basewords(option.name))

            for answer in question.answer_set.all():
                if(answer.explanation is None): continue
                words.extend(text_to_basewords(answer.explanation))

            cache[name] = ' '.join(words)
        else:
            words = cache[name].split(' ')

        lexicon.add(*words)

        itemlexicon = Lexicon()
        itemlexicon.add(*words)
        questions[question] = itemlexicon

    sessions = {}
    handled = []
    session_objects = Session.objects.filter(subject__contains=u'Hyv')
    n_sessions = session_objects.count()
    for (i, session) in enumerate(session_objects):
        #if session.info in handled:
        #    continue
        #handled.append(session.info)
        print >>sys.stderr, "Handling session %i/%i"%(i+1, n_sessions)
        # TODO: Filter by actual period

        if session.plenary_session.date.year < 2007:
            continue

        words = get_session_word_features(session, cache, docs)
       
        if len(words) == 0:
            continue

        lexicon.add(*words)

        itemlexicon = Lexicon()
        itemlexicon.add(*words)
        sessions[session] = itemlexicon
        
    prod = itertools.product(questions.keys(), sessions.keys())
    minr = 1
    maxr = 0
    relevances = []
    for (question, session) in prod:
        relevance = lexicon_relevance(questions[question], sessions[session],
                                      lexicon)
        if relevance < minr:
            minr = relevance
        if relevance > maxr:
            maxr = relevance
        relevances.append((relevance, question, session))

    # TODO: This is not very nice, we should have a better
    # ....relevancy measure instead
    relevances = map(lambda (r, q, s): ((r - minr) / (maxr - minr), q, s),
                     relevances)

    for (relevance, question, session) in relevances:
        try:
            record = QuestionSessionRelevance.objects.get(
                            question=question,
                            session=session, user=None)
        except QuestionSessionRelevance.DoesNotExist:
            record = QuestionSessionRelevance(relevance=relevance,
                        question=question,
                        session=session, user=None)
        
        record.relevance = relevance
        record.save()

if __name__ == '__main__':
    docs = None
    if(len(sys.argv) > 1):
        docs = shelve.open(sys.argv[1], 'r')
    estimate_relations(docs=docs)

