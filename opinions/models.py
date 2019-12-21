#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.db import models, connection, transaction
from kamu.votes.models import Member, Party, Session, Vote
from django.contrib.auth.models import User
from django.conf import settings 

class QuestionSource(models.Model):
    name = models.CharField(max_length=255)
    year = models.IntegerField()
    url_name = models.SlugField(unique=True)

    class Meta:
        unique_together = (('name', 'year'), )

    def __unicode__(self):
        return self.url_name

class QuestionManager(models.Manager):
    def get_by_url_name(self, url_name):
        if not '/' in url_name:
            raise Question.DoesNotExist()
        src, order = url_name.split('/')
        try:
            order = int(order)
        except ValueError:
            raise Question.DoesNotExist()
        return self.get(order=order, source__url_name=src)

class Question(models.Model):
    text = models.TextField()
    source = models.ForeignKey(QuestionSource, on_delete=models.CASCADE)
    order = models.IntegerField()

    objects = QuestionManager()

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
        ordering = ('-source__year', 'source__name', 'order', )
        unique_together = (('order', 'source'), )

    @models.permalink
    def get_absolute_url(self):
        args = {'source': self.source.url_name, 'question': self.order}
        return ('opinions.views.show_question', (), args)

    def __unicode__(self):
        return "%s/%d" % (self.source, self.order)

class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    order = models.IntegerField()

    class Meta:
        unique_together = (('question', 'order'), )
        ordering = ('question__order', 'order')

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
        return '%s: %s' % (self.question, self.name)

class Answer(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    option = models.ForeignKey(Option, on_delete=models.CASCADE, null=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    explanation = models.TextField(null=True)

    class Meta:
        unique_together = (('member', 'option'), )

    def __unicode__(self):
        return '%s %s' % (self.member, self.option)

class VoteOptionCongruenceManager(models.Manager):
    def user_has_congruences(self, user):
        if not user.is_authenticated():
            return False
        return self.filter(user=user).count() > 0

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
        
        cong_user = self.get_congruence_user(for_user)
        if cong_user is not None:
            args.append(cong_user.id)
            extra_where += "AND c.user_id=%s\n"

        if (for_question is not None):
            args.append(for_question.id)
            extra_where += "AND o.question_id=%s\n"
        
        session_freq_query = \
            """
            SELECT session_id, COUNT(session_id) AS freq
               FROM opinions_voteoptioncongruence
               GROUP BY session_id
            """


        query = \
            """
                SELECT
                    SUM(congruence/f.freq)/SUM(ABS(congruence/f.freq)) AS congruence_avg
                  FROM
                    opinions_voteoptioncongruence AS c,
                    opinions_answer AS a,
                    opinions_option AS o,
                    votes_vote AS v,
                    (%s) AS f
                  WHERE v.session_id=c.session_id
                    AND f.session_id=c.session_id
                    AND a.option_id=c.option_id
                    AND a.member_id=v.member_id
                    AND v.vote=c.vote
                    AND o.id=a.option_id
                    %s
                    AND %s=%%s
                  """ \
            % (session_freq_query, extra_where, id_field)
        
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

    def get_congruence_user(self, for_user):
        if(for_user is None): return None

        if (not VoteOptionCongruence.objects.user_has_congruences(for_user)):
            magic_user = VoteOptionCongruence.magic_username
            for_user = User.objects.get(username=magic_user)
        return for_user

    def __get_average_congruences(self, grouping_class, id_field,
                                  descending=True, limit=False, for_user=None,
                                  for_question=None, for_member=None,
                                  for_session=None,
                                  allow_null_congruences=False,
                                  raw_average=False):
        
        session_freq_query = \
            """
            SELECT session_id, COUNT(session_id) AS freq
               FROM opinions_voteoptioncongruence
               GROUP BY session_id
            """
        
        avg = "SUM(congruence/f.freq)/SUM(ABS(congruence/f.freq)) AS congruence_avg"
        if(raw_average):
            avg = "AVG(congruence) AS congruence_avg"


        query = \
            """
                SELECT %s.*,
                    %s
                  FROM
                    opinions_voteoptioncongruence as c,
                    opinions_answer as a,
                    opinions_option as o,
                    votes_vote AS v,
                    (%s) AS f,
                    %s
                  WHERE v.session_id=c.session_id
                    AND f.session_id=c.session_id
                    AND a.option_id=c.option_id
                    AND a.member_id=v.member_id
                    AND v.vote=c.vote
                    AND o.id=a.option_id
                    AND %s.%s=%s
                    %%s
                  GROUP BY %s
                  HAVING congruence_avg IS NOT NULL
                  ORDER BY congruence_avg %s
                  %s
                  """ \
            % (grouping_class._meta.db_table,
               avg,
               session_freq_query,
               grouping_class._meta.db_table,
               grouping_class._meta.db_table,
               grouping_class._meta.pk.name,
               id_field,
               id_field,
               ('ASC', 'DESC')[descending],
               ('', 'LIMIT %i' % (int(limit), ))[bool(limit)])

        extra_where = ''
        query_args = []
        
        cong_user = self.get_congruence_user(for_user)
        if cong_user is not None:
            query_args.append(cong_user.id)
            extra_where += "AND c.user_id=%s\n"

        if for_question is not None:
            query_args.append(for_question.id)
            extra_where += "AND o.question_id=%s\n"

        if for_member is not None:
            query_args.append(for_member.id)
            extra_where += "AND a.member_id=%s\n"

        if for_session is not None:
            query_args.append(for_session.id)
            extra_where += "AND v.session_id=%s\n"

        query = query % extra_where

        if(allow_null_congruences):
            nullquery = \
                """
                SELECT *, NULL as congruence_avg
                FROM %s
                """ % (grouping_class._meta.db_table,)
            query = """
                %s UNION (%s)
                  ORDER BY
                    ISNULL(congruence_avg),
                    congruence_avg %s
                """%(nullquery, query, ('ASC', 'DESC')[descending])

        return grouping_class.objects.raw(query, query_args)

    def get_party_congruences(self, **kwargs):
        return self.__get_average_congruences(Party, 'v.party', **kwargs)

    def get_member_congruences(self, **kwargs):
        return self.__get_average_congruences(Member, 'v.member_id', **kwargs)

    def get_question_congruences(self, **kwargs):
        return self.__get_average_congruences(Question, 'a.question_id', **kwargs)

    def get_session_congruences(self, **kwargs):
        return self.__get_average_congruences(Session, 'v.session_id', **kwargs)

    def get_vote_congruences(self, for_member=None, for_party=None,
                                    for_user=None):
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
            
        cong_user = self.get_congruence_user(for_user)
        if cong_user is not None:
            args.append(cong_user.id)
            extra_where += "AND c.user_id=%s\n"

        session_freq_query = \
            """
            SELECT session_id, COUNT(session_id) AS freq
               FROM opinions_voteoptioncongruence
               GROUP BY session_id
            """
        
        query = \
        """
        SELECT
          c.congruence/f.freq, c.*
        FROM
          opinions_voteoptioncongruence AS c,
          votes_vote AS v,
          opinions_answer AS a,
          (%(session_freq)s) AS f
        WHERE
          c.session_id=v.session_id AND
          f.session_id=c.session_id AND
          c.vote=v.vote AND
          v.member_id=a.member_id AND
          a.option_id=c.option_id AND
          c.congruence <> 0
          %(extra_where)s
        ORDER BY
          a.question_id, c.option_id
        """ % {'session_freq': session_freq_query, 'extra_where': extra_where}
        return VoteOptionCongruence.objects.raw(query, args)


class VoteOptionCongruence(models.Model):
    option = models.ForeignKey(Option, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    vote = models.CharField(max_length=1, choices=Vote.VOTE_CHOICES,
                            db_index=True)
    congruence = models.FloatField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    objects = VoteOptionCongruenceManager()
    
    magic_username = settings.KAMU_OPINIONS_MAGIC_USER


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

    def __unicode__(self):
        args = (self.option.question.source, self.option.question.order,
                self.option.order, self.vote, self.user, self.congruence)
        return "%s/%d/%d-%s (%s): %0.02f" % args

    class Meta:
        unique_together = (('user', 'option', 'session', 'vote'), )

class QuestionSessionRelevance(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    relevance = models.FloatField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

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

