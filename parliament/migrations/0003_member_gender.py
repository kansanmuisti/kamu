# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('parliament', '0002_auto_20150207_1510'),
    ]

    operations = [
        migrations.AddField(
            model_name='member',
            name='gender',
            field=models.CharField(max_length=1, null=True, blank=True),
            preserve_default=True,
        ),
    ]
