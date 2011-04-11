#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.db import models, connection, transaction
from kamu.votes.models import Member, Party, Session, Vote
from django.contrib.auth.models import User

class QuestionSource(models.Model):
    name = models.CharField(max_length=255)
    year = models.IntegerField()
    url_name = models.SlugField(unique=True)

    class Meta:
        unique_together = (('name', 'year'), )

    def __unicode__(self):
        return u'%s (%i)' % (self.name, self.year)

class Question(models.Model):
    text = models.TextField()
    source = models.ForeignKey(QuestionSource)
    order = models.IntegerField()

    def save(self, *args, **kwargs):
        if self.order is None:
            q = Question.objects.filter(source=self.source)
            max_order = q.aggregate(models.Max('order'))['order__max']
            if max_order is None:
                max_order = 0
            self.order = int(max_order) + 1

        super(Question, self).save(*args, **kwargs)

    def answers(self):
        options = self.option_set.all()
        return Answer.objects.filter(option__in=options)

    class Meta:
        ordering = ('-order', )
        unique_together = (('order', 'source'), )

    def __unicode__(self):
        return self.text

class Option(models.Model):
    question = models.ForeignKey(Question)
    name = models.CharField(max_length=255)
    order = models.IntegerField()

    class Meta:
        unique_together = (('question', 'order'), )
        ordering = ('-question__order', '-order')

    def save(self, *args, **kwargs):
        if self.order is None:
            q = Option.objects.filter(question=self.question)
            max_order = q.aggregate(models.Max('order'))['order__max']
            if max_order is None:
                max_order = 0
            self.order = int(max_order) + 1

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

class VoteOptionCongruenceManager(models.Manager):
    def get_congruence(self, option, session, vote='Y'):
        congruence = VoteOptionCongruence.objects.filter(
                                option=option, session=session,
                                vote=vote)
        if congruence.count() == 0:
            return None
        congruence = congruence.aggregate(models.Avg('congruence'))
        return congruence['congruence__avg']

    def __get_average_congruence(self, grouping_object, id_field,
                                 for_user=None, for_question=None):
        args = []
        extra_where = ""
        if (for_user is not None and for_user.is_authenticated()):
            args.append(for_user.id)
            extra_where += "AND c.user_id=%s\n"

        if (for_question is not None):
            args.append(for_question.id)
            extra_where += "AND o.question_id=%s\n"

        query = \
            """
                SELECT
                    SUM(congruence)/SUM(ABS(congruence)) AS congruence_avg
                  FROM
                    opinions_voteoptioncongruence AS c,
                    opinions_answer AS a,
                    opinions_option AS o,
                    votes_vote AS v
                  WHERE v.session_id=c.session_id
                    AND a.option_id=c.option_id
                    AND a.member_id=v.member_id
                    AND v.vote=c.vote
                    AND o.id=a.option_id
                    %s
                    AND %s=%%s
                  """ \
            % (extra_where, id_field)
        
        args.append(grouping_object.pk)
        cursor = connection.cursor()
        count = cursor.execute(query, args)
        if count < 1:
            return None
        return cursor.fetchone()[0]

    def get_member_congruence(self, member, **kargs):
        return self.__get_average_congruence(member, 'v.member_id', **kargs)

    def get_party_congruence(self, party, **kargs):
        return self.__get_average_congruence(party, 'v.party', **kargs)

    def get_question_congruence(self, question, **kargs):
        return self.__get_average_congruence(question, 'a.question_id', **kargs)

    def __get_average_congruences(self, grouping_class, id_field,
                                  descending=True, limit=False, for_user=None,
                                  for_question=None, for_member=None):
        query = \
            """
                SELECT %s AS %s,
                    SUM(congruence)/SUM(ABS(congruence)) AS congruence_avg
                  FROM
                    opinions_voteoptioncongruence as c,
                    opinions_answer as a,
                    opinions_option as o,
                    votes_vote AS v
                  WHERE v.session_id=c.session_id
                    AND a.option_id=c.option_id
                    AND a.member_id=v.member_id
                    AND v.vote=c.vote
                    AND o.id=a.option_id
                    %%s
                  GROUP BY %s
                  HAVING congruence_avg IS NOT NULL
                  ORDER BY congruence_avg %s
                  %s
                  """ \
            % (id_field, grouping_class._meta.pk.name,
               id_field,
               ('ASC', 'DESC')[descending],
               ('', 'LIMIT %i' % (int(limit), ))[bool(limit)])

        extra_where = ''
        query_args = []
        if (for_user is not None and for_user.is_authenticated()):
            query_args.append(for_user.id)
            extra_where += "AND c.user_id=%s\n"

        if for_question is not None:
            query_args.append(for_question.id)
            extra_where += "AND o.question_id=%s\n"

        if for_member is not None:
            query_args.append(for_member.id)
            extra_where += "AND a.member_id=%s\n"

        query = query % extra_where
        return grouping_class.objects.raw(query, query_args)

    def get_party_congruences(self, **kwargs):
        return self.__get_average_congruences(Party, 'v.party', **kwargs)

    def get_member_congruences(self, **kwargs):
        return self.__get_average_congruences(Member, 'v.member_id', **kwargs)

    def get_question_congruences(self, **kwargs):
        return self.__get_average_congruences(Question, 'a.question_id', **kwargs)

    def get_session_congruences(self, **kwargs):
        return self.__get_average_congruences(Session, 'v.session_id', **kwargs)

    def get_vote_congruences(self, for_member=None, for_party=None):
        # This could maybe be done without SQL, but my brain
        # doesn't work enough for that at the moment
        extra_where = ''
        args = []
        if for_member is not None:
            extra_where += "AND v.member_id=%s\n"
            args.append(for_member.pk)

        if for_party is not None:
            extra_where += "AND v.party=%s"
            args.append(for_party.pk)

        query = \
        """
        SELECT
          c.*
        FROM
          opinions_voteoptioncongruence AS c,
          votes_vote AS v,
          opinions_answer AS a
        WHERE
          c.session_id=v.session_id AND
          c.vote=v.vote AND
          v.member_id=a.member_id AND
          a.option_id=c.option_id AND
          c.congruence <> 0
          %s
        ORDER BY
          a.question_id, c.option_id
        """ % (extra_where, )
        return VoteOptionCongruence.objects.raw(query, args)


class VoteOptionCongruence(models.Model):
    option = models.ForeignKey(Option)
    session = models.ForeignKey(Session)
    vote = models.CharField(max_length=1, choices=Vote.VOTE_CHOICES,
                            db_index=True)
    congruence = models.FloatField()
    user = models.ForeignKey(User)

    objects = VoteOptionCongruenceManager()

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

