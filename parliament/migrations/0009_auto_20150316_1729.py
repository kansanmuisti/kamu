# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('parliament', '0008_auto_20150316_1541'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='memberactivity',
            index_together=set([('member', 'time')]),
        ),
    ]
