# -*- coding: utf-8 -*-


from django.db import models, migrations
from sortedm2m.operations import AlterSortedManyToManyField
import sortedm2m.fields


class Migration(migrations.Migration):

    dependencies = [
        ('parliament', '0001_initial'),
    ]

    operations = [
        AlterSortedManyToManyField(
            model_name='document',
            name='keywords',
            field=sortedm2m.fields.SortedManyToManyField(help_text=None, to='parliament.Keyword'),
            preserve_default=True,
        ),
    ]
