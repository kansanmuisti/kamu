#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.contrib import admin
from .models import Question, Option, Answer

admin.site.register(Question)
admin.site.register(Option)
admin.site.register(Answer)

