# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('parliament', '0004_memberactivity_last_modified_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='answer',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='document',
            name='question',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
