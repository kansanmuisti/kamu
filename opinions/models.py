#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.db import models
from kamu.votes.models import Member

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

    def __unicode__(self):
        return u'%s: %s' % (self.question, self.name)

class Answer(models.Model):
    member = models.ForeignKey(Member)
    option = models.ForeignKey(Option, null=True)
    explanation = models.TextField()

    class Meta:
        unique_together = (('member', 'option'), )

    def __unicode__(self):
        return u'%s %s' % (self.member, self.option)

