# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('parliament', '0007_plenarysessionitemdocument_stage'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='vote',
            index_together=set([('session', 'vote')]),
        ),
    ]
