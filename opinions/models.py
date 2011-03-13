#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.db import models, connection, transaction
from kamu.votes.models import Member, Party, Session, Vote
from django.contrib.auth.models import User

class QuestionSource(models.Model):
    name = models.CharField(max_length=255)
    year = models.IntegerField()

    class Meta:
        unique_together = (('name', 'year'), )

    def __unicode__(self):
        return u'%s (%i)' % (self.name, self.year)

class Question(models.Model):
    text = models.TextField()
    source = models.ForeignKey(QuestionSource)
    weight = models.IntegerField(unique=True)

    def save(self, *args, **kwargs):
        if self.weight is None:
            q = Question.objects.filter(source=self.source)
            max_weight = q.aggregate(models.Max('weight'))['weight__max']
            if max_weight is None:
                max_weight = 0
            self.weight = int(max_weight) + 1

        super(Question, self).save(*args, **kwargs)

    def answers(self):
        options = self.option_set.all()
        return Answer.objects.filter(option__in=options)

    class Meta:
        ordering = ('-weight', )
        unique_together = (('weight', 'source'), )

    def __unicode__(self):
        return self.text

class Option(models.Model):
    question = models.ForeignKey(Question)
    name = models.CharField(max_length=255)
    weight = models.IntegerField()

    class Meta:
        unique_together = (('question', 'weight'), )
        ordering = ('-question__weight', '-weight')

    def save(self, *args, **kwargs):
        if self.weight is None:
            q = Option.objects.filter(question=self.question)
            max_weight = q.aggregate(models.Max('weight'))['weight__max']
            if max_weight is None:
                max_weight = 0
            self.weight = int(max_weight) + 1

        super(Option, self).save(*args, **kwargs)

    def party_shares(self):

        # Ah, SQL is so nice and terse

        query = \
            """
            SELECT votes_party.*,
               ROUND(COALESCE(partyvotes/partytotal, 0)*100) AS share
            FROM
             (SELECT party_id, count(*) as partytotal
              FROM opinions_answer, votes_member
              WHERE opinions_answer.question_id=%s
                AND votes_member.id=opinions_answer.member_id
              GROUP BY votes_member.party_id) as totals,
             (SELECT votes_member.party_id, count(*) AS partyvotes
              FROM opinions_answer, votes_member
              WHERE opinions_answer.option_id=%s
                AND opinions_answer.member_id=votes_member.id
                GROUP BY votes_member.party_id) as stats
            RIGHT JOIN votes_party ON votes_party.name=stats.party_id
            WHERE votes_party.name = totals.party_id
            """
        return Party.objects.raw(query, [self.question_id, self.id])

    def __unicode__(self):
        return u'%s: %s' % (self.question, self.name)

class Answer(models.Model):
    member = models.ForeignKey(Member)
    option = models.ForeignKey(Option, null=True)
    question = models.ForeignKey(Question)
    explanation = models.TextField()

    class Meta:
        unique_together = (('member', 'option'), )

    def __unicode__(self):
        return u'%s %s' % (self.member, self.option)

class VoteOptionCongruence(models.Model):
    option = models.ForeignKey(Option)
    session = models.ForeignKey(Session)
    vote = models.CharField(max_length=1, choices=Vote.VOTE_CHOICES,
                            db_index=True)
    congruence = models.FloatField()
    user = models.ForeignKey(User)

    def save(self, update_if_exists=False, **kwargs):
        if update_if_exists:
            congruence = self.congruence
            self.congruence = None
            matches = VoteOptionCongruence.objects.filter(user=self.user,
                    option=self.option, session=self.session, vote=self.vote)
            if matches.count() > 0:
                self = matches[0]
            self.congruence = congruence

        return models.Model.save(self, **kwargs)

    @classmethod
    def get_congruence(
        cls,
        option,
        session,
        vote='Y',
        ):
        congruence = cls.objects.filter(option=option, session=session,
                vote=vote)
        if congruence.count() == 0:
            return None
        congruence = congruence.aggregate(models.Avg('congruence'))
        return congruence['congruence__avg']

    class Meta:
        unique_together = (('user', 'option', 'session', 'vote'), )

class QuestionSessionRelevance(models.Model):
    question = models.ForeignKey(Question)
    session = models.ForeignKey(Session)
    relevance = models.FloatField()
    user = models.ForeignKey(User, blank=True, null=True)

    @classmethod
    def get_relevant_sessions(cls, question):
        query = \
            """
                SELECT votes_session.id, SQRT(AVG(relevance)) AS question_relevance
                FROM
                  (SELECT session_id, relevance
                     FROM opinions_questionsessionrelevance
                     WHERE question_id=%s
                   UNION ALL
                   SELECT session_id, ABS(congruence) AS relevance
                     FROM opinions_voteoptioncongruence, opinions_option
                     WHERE opinions_option.id=option_id AND question_id=%s) 
                  as merged, votes_session
                 WHERE votes_session.id = session_id
                 GROUP BY session_id ORDER BY question_relevance DESC
                 """
        return Session.objects.raw(query, [question.id] * 2)

    class Meta:
        unique_together = (('question', 'session', 'user'), )

