# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('parliament', '0006_auto_20150312_2248'),
    ]

    operations = [
        migrations.AddField(
            model_name='plenarysessionitemdocument',
            name='stage',
            field=models.CharField(max_length=50, null=True, blank=True),
            preserve_default=True,
        ),
    ]
