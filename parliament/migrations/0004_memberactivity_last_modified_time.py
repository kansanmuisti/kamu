# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('parliament', '0003_member_gender'),
    ]

    operations = [
        migrations.AddField(
            model_name='memberactivity',
            name='last_modified_time',
            field=models.DateTimeField(null=True),
            preserve_default=True,
        ),
    ]
