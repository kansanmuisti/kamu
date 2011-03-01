#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.db import models, connection, transaction
from kamu.votes.models import Member,Party

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
        unique_together = (('weight', 'source'),)

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
	query = """
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

