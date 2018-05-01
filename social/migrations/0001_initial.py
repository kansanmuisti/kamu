# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ApiToken',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=2, choices=[(b'TW', b'Twitter'), (b'FB', b'Facebook')])),
                ('token', models.CharField(max_length=100)),
                ('updated_time', models.DateTimeField(auto_now=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BrokenFeed',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=2, choices=[(b'TW', b'Twitter'), (b'FB', b'Facebook')])),
                ('origin_id', models.CharField(max_length=100, db_index=True)),
                ('account_name', models.CharField(max_length=100, null=True)),
                ('check_time', models.DateTimeField(auto_now=True)),
                ('reason', models.CharField(max_length=50)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Feed',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=2, choices=[(b'TW', b'Twitter'), (b'FB', b'Facebook')])),
                ('origin_id', models.CharField(max_length=50, db_index=True)),
                ('interest', models.PositiveIntegerField(null=True)),
                ('picture', models.URLField(max_length=250, null=True)),
                ('account_name', models.CharField(max_length=50, null=True)),
                ('last_update', models.DateTimeField(null=True, db_index=True)),
                ('update_error_count', models.PositiveIntegerField(default=0)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Update',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.TextField(null=True)),
                ('type', models.CharField(max_length=30)),
                ('sub_type', models.CharField(max_length=30, null=True)),
                ('created_time', models.DateTimeField(db_index=True)),
                ('origin_id', models.CharField(max_length=50, db_index=True)),
                ('origin_data', models.TextField(help_text=b'Raw dump of all data from source', null=True)),
                ('interest', models.PositiveIntegerField(null=True)),
                ('picture', models.URLField(max_length=350, null=True)),
                ('share_link', models.URLField(max_length=350, null=True)),
                ('share_title', models.CharField(max_length=250, null=True)),
                ('share_caption', models.CharField(max_length=600, null=True)),
                ('share_description', models.TextField(null=True)),
                ('last_modified_time', models.DateTimeField(db_index=True, auto_now=True, null=True)),
                ('feed', models.ForeignKey(to='social.Feed')),
            ],
            options={
                'ordering': ['-created_time'],
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='update',
            unique_together=set([('feed', 'origin_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='feed',
            unique_together=set([('type', 'origin_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='brokenfeed',
            unique_together=set([('type', 'origin_id')]),
        ),
    ]
