# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('social', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Committee',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('last_modified_time', models.DateTimeField(null=True)),
                ('last_checked_time', models.DateTimeField(null=True)),
                ('name', models.CharField(help_text=b'Name of the committee', unique=True, max_length=100)),
                ('description', models.CharField(help_text=b'Description of the committee', max_length=500, null=True)),
                ('origin_id', models.CharField(help_text=b'Upstream identifier (in URL)', max_length=20, unique=True, null=True)),
                ('current', models.BooleanField(default=True, help_text=b'Is the committee current or past')),
                ('url_name', models.CharField(help_text=b'Name identifier for URLs', max_length=100, unique=True, null=True)),
            ],
            options={
                'ordering': ('name',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CommitteeAssociation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('begin', models.DateField()),
                ('end', models.DateField(db_index=True, null=True, blank=True)),
                ('role', models.CharField(max_length=15, null=True, choices=[(b'chairman', 'Chairman'), (b'deputy-cm', 'Deputy Chairman'), (b'member', 'Member'), (b'deputy-m', 'Deputy Member')])),
                ('committee', models.ForeignKey(to='parliament.Committee')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='District',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50, db_index=True)),
                ('long_name', models.CharField(max_length=50, null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DistrictAssociation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50, null=True, blank=True)),
                ('begin', models.DateField()),
                ('end', models.DateField(null=True, blank=True)),
                ('district', models.ForeignKey(to='parliament.District', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('last_modified_time', models.DateTimeField(null=True)),
                ('last_checked_time', models.DateTimeField(null=True)),
                ('type', models.CharField(db_index=True, max_length=30, choices=[(b'mp_prop', 'MP law proposal'), (b'gov_bill', 'Government bill'), (b'written_ques', 'Written question'), (b'interpellation', 'Interpellation')])),
                ('name', models.CharField(unique=True, max_length=30, db_index=True)),
                ('origin_id', models.CharField(unique=True, max_length=30, db_index=True)),
                ('url_name', models.SlugField(unique=True, max_length=20)),
                ('date', models.DateField(null=True, blank=True)),
                ('info_link', models.URLField(null=True, blank=True)),
                ('sgml_link', models.URLField(null=True, blank=True)),
                ('subject', models.TextField()),
                ('summary', models.TextField(null=True, blank=True)),
                ('version', models.CharField(max_length=10, null=True)),
                ('error', models.CharField(max_length=50, null=True, blank=True)),
            ],
            options={
                'ordering': ('date',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DocumentProcessingStage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('index', models.PositiveSmallIntegerField()),
                ('stage', models.CharField(db_index=True, max_length=15, choices=[(b'intro', 'Introduced'), (b'debate', 'Debate'), (b'committee', 'In committee'), (b'agenda', 'On agenda'), (b'1stread', 'First reading'), (b'2ndread', 'Second reading'), (b'3rdread', 'Third reading'), (b'finished', 'Finished'), (b'onlyread', 'Only reading'), (b'only2read', 'Only and 2nd reading'), (b'only3read', 'Only and 3rd reading'), (b'cancelled', 'Cancelled'), (b'lapsed', 'Lapsed'), (b'suspended', 'Suspended'), (b'ministry', 'In ministry')])),
                ('date', models.DateField()),
                ('doc', models.ForeignKey(to='parliament.Document')),
            ],
            options={
                'ordering': ('doc', 'index'),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DocumentSignature',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
                ('doc', models.ForeignKey(to='parliament.Document')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Funding',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=6, choices=[(b'own', 'Own funds'), (b'co', 'Corporation'), (b'ind', 'Individual'), (b'loan', 'Loan'), (b'u_ind', 'Undefined individuals'), (b'u_com', 'Undefined communities'), (b'party', 'Party'), (b'oth', 'Other')])),
                ('amount', models.DecimalField(max_digits=10, decimal_places=2)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FundingSource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=120, null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GoverningParty',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('begin', models.DateField(help_text=b'Beginning of government participation')),
                ('end', models.DateField(help_text=b'End of government participation', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Government',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('begin', models.DateField(help_text=b'Date when the government began operations')),
                ('end', models.DateField(help_text=b'End date for the government', null=True)),
                ('name', models.CharField(help_text=b'Descriptive name for this government, depends on national custom', max_length=50)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Keyword',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=128, db_index=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='KeywordActivity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='KeywordActivityScore',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('score', models.PositiveIntegerField()),
                ('calc_time', models.DateTimeField(auto_now=True)),
                ('keyword', models.ForeignKey(to='parliament.Keyword')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Member',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('last_modified_time', models.DateTimeField(null=True)),
                ('last_checked_time', models.DateTimeField(null=True)),
                ('name', models.CharField(unique=True, max_length=50)),
                ('origin_id', models.CharField(db_index=True, max_length=20, unique=True, null=True, blank=True)),
                ('url_name', models.SlugField(unique=True)),
                ('birth_date', models.DateField(null=True, blank=True)),
                ('birth_place', models.CharField(max_length=50, null=True, blank=True)),
                ('given_names', models.CharField(max_length=50)),
                ('surname', models.CharField(max_length=50)),
                ('summary', models.TextField(null=True)),
                ('email', models.EmailField(max_length=75, null=True, blank=True)),
                ('phone', models.CharField(max_length=20, null=True, blank=True)),
                ('photo', models.ImageField(upload_to=b'images/members')),
                ('info_link', models.URLField()),
                ('wikipedia_link', models.URLField(null=True, blank=True)),
                ('homepage_link', models.URLField(null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MemberActivity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('time', models.DateTimeField(db_index=True)),
            ],
            options={
                'ordering': ('time', 'member__name'),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='InitiativeActivity',
            fields=[
                ('memberactivity_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='parliament.MemberActivity')),
                ('doc', models.ForeignKey(to='parliament.Document')),
            ],
            options={
            },
            bases=('parliament.memberactivity',),
        ),
        migrations.CreateModel(
            name='CommitteeDissentActivity',
            fields=[
                ('memberactivity_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='parliament.MemberActivity')),
            ],
            options={
            },
            bases=('parliament.memberactivity',),
        ),
        migrations.CreateModel(
            name='MemberActivityType',
            fields=[
                ('type', models.CharField(max_length=5, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('weight', models.FloatField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MemberSeat',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('begin', models.DateField()),
                ('end', models.DateField(null=True, blank=True)),
                ('member', models.ForeignKey(to='parliament.Member')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MemberSocialFeed',
            fields=[
                ('feed_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='social.Feed')),
                ('member', models.ForeignKey(to='parliament.Member')),
            ],
            options={
            },
            bases=('social.feed',),
        ),
        migrations.CreateModel(
            name='MemberStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('begin', models.DateField()),
                ('end', models.DateField(null=True, blank=True)),
                ('party_agreement', models.CommaSeparatedIntegerField(max_length=20)),
                ('session_agreement', models.CommaSeparatedIntegerField(max_length=20)),
                ('vote_counts', models.CommaSeparatedIntegerField(max_length=30)),
                ('statement_count', models.IntegerField()),
                ('election_budget', models.DecimalField(null=True, max_digits=10, decimal_places=2, blank=True)),
                ('member', models.ForeignKey(to='parliament.Member')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MinistryAssociation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('begin', models.DateField()),
                ('end', models.DateField(db_index=True, null=True, blank=True)),
                ('label', models.CharField(help_text=b'Official descriptive name of the position. eg. minister of of International Development', max_length=50)),
                ('role', models.CharField(help_text=b'Position of the official. eg. minister.', max_length=20, choices=[(b'minister', 'Minister')])),
                ('member', models.ForeignKey(to='parliament.Member')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Party',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('last_modified_time', models.DateTimeField(null=True)),
                ('last_checked_time', models.DateTimeField(null=True)),
                ('abbreviation', models.CharField(unique=True, max_length=10, db_index=True)),
                ('name', models.CharField(max_length=50)),
                ('logo', models.ImageField(upload_to=b'images/parties')),
                ('homepage_link', models.URLField()),
                ('vis_color', models.CharField(max_length=15, null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PartyAssociation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50, null=True, blank=True)),
                ('begin', models.DateField()),
                ('end', models.DateField(null=True, blank=True)),
                ('member', models.ForeignKey(to='parliament.Member')),
                ('party', models.ForeignKey(to='parliament.Party', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PlenarySession',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('last_modified_time', models.DateTimeField(null=True)),
                ('last_checked_time', models.DateTimeField(null=True)),
                ('name', models.CharField(max_length=20)),
                ('date', models.DateField(db_index=True)),
                ('info_link', models.URLField()),
                ('url_name', models.SlugField(unique=True, max_length=20)),
                ('origin_id', models.CharField(db_index=True, max_length=50, null=True, blank=True)),
                ('origin_version', models.CharField(max_length=10, null=True, blank=True)),
            ],
            options={
                'ordering': ('-date',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PlenarySessionItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('number', models.PositiveIntegerField()),
                ('sub_number', models.PositiveIntegerField(null=True, blank=True)),
                ('type', models.CharField(max_length=15, choices=[(b'agenda', 'Agenda item'), (b'question', 'Question time'), (b'budget', 'Budget proposal')])),
                ('description', models.CharField(max_length=1000)),
                ('sub_description', models.CharField(max_length=100, null=True, blank=True)),
                ('processing_stage', models.CharField(db_index=True, max_length=20, null=True, blank=True)),
                ('nr_votes', models.IntegerField(db_index=True, null=True, blank=True)),
                ('nr_statements', models.IntegerField(db_index=True, null=True, blank=True)),
            ],
            options={
                'ordering': ('-plsess__date', '-number', '-sub_number'),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PlenarySessionItemDocument',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.PositiveIntegerField()),
                ('doc', models.ForeignKey(to='parliament.Document')),
                ('item', models.ForeignKey(to='parliament.PlenarySessionItem')),
            ],
            options={
                'ordering': ('order',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PlenaryVote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('last_modified_time', models.DateTimeField(null=True)),
                ('last_checked_time', models.DateTimeField(null=True)),
                ('number', models.IntegerField()),
                ('time', models.DateTimeField()),
                ('subject', models.TextField()),
                ('setting', models.CharField(max_length=200)),
                ('info_link', models.URLField(null=True, blank=True)),
                ('vote_counts', models.CommaSeparatedIntegerField(max_length=20, null=True, blank=True)),
            ],
            options={
                'ordering': ('plsess__date', 'number'),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PlenaryVoteDocument',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.PositiveIntegerField()),
                ('doc', models.ForeignKey(to='parliament.Document')),
                ('session', models.ForeignKey(to='parliament.PlenaryVote')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RebelVoteActivity',
            fields=[
                ('memberactivity_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='parliament.MemberActivity')),
            ],
            options={
            },
            bases=('parliament.memberactivity',),
        ),
        migrations.CreateModel(
            name='Seat',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('row', models.IntegerField()),
                ('seat', models.IntegerField()),
                ('x', models.FloatField()),
                ('y', models.FloatField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SignatureActivity',
            fields=[
                ('memberactivity_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='parliament.MemberActivity')),
                ('signature', models.ForeignKey(to='parliament.DocumentSignature', unique=True)),
            ],
            options={
            },
            bases=('parliament.memberactivity',),
        ),
        migrations.CreateModel(
            name='SocialUpdateActivity',
            fields=[
                ('memberactivity_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='parliament.MemberActivity')),
                ('update', models.ForeignKey(to='social.Update', unique=True)),
            ],
            options={
            },
            bases=('parliament.memberactivity',),
        ),
        migrations.CreateModel(
            name='SpeakerAssociation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('begin', models.DateField()),
                ('end', models.DateField(db_index=True, null=True, blank=True)),
                ('role', models.CharField(help_text=b'Speaker position', max_length=20, choices=[(b'speaker', 'Speaker'), (b'1st-deputy-speaker', '1st Deputy Speaker'), (b'2nd-deputy-speaker', '2st Deputy Speaker')])),
                ('member', models.ForeignKey(to='parliament.Member')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Statement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('index', models.PositiveIntegerField(db_index=True)),
                ('speaker_name', models.CharField(max_length=40, null=True, blank=True)),
                ('speaker_role', models.CharField(max_length=40, null=True, blank=True)),
                ('type', models.CharField(max_length=15, choices=[(b'normal', b'Statement'), (b'speaker', b'Speaker statement')])),
                ('text', models.TextField()),
                ('item', models.ForeignKey(to='parliament.PlenarySessionItem')),
                ('member', models.ForeignKey(to='parliament.Member', null=True)),
            ],
            options={
                'ordering': ('item', 'index'),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StatementActivity',
            fields=[
                ('memberactivity_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='parliament.MemberActivity')),
                ('statement', models.ForeignKey(to='parliament.Statement', unique=True)),
            ],
            options={
            },
            bases=('parliament.memberactivity',),
        ),
        migrations.CreateModel(
            name='Term',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=40)),
                ('display_name', models.CharField(max_length=40)),
                ('begin', models.DateField()),
                ('end', models.DateField(null=True, blank=True)),
                ('visible', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ('-begin',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TermMember',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('election_budget', models.DecimalField(null=True, max_digits=10, decimal_places=2, blank=True)),
                ('member', models.ForeignKey(to='parliament.Member')),
                ('term', models.ForeignKey(to='parliament.Term')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('vote', models.CharField(db_index=True, max_length=1, choices=[(b'Y', 'Yes'), (b'N', 'No'), (b'A', 'Absent'), (b'E', 'Empty'), (b'S', 'Speaker')])),
                ('party', models.CharField(max_length=10)),
                ('member', models.ForeignKey(to='parliament.Member')),
                ('session', models.ForeignKey(to='parliament.PlenaryVote')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='statement',
            unique_together=set([('item', 'index')]),
        ),
        migrations.AlterUniqueTogether(
            name='seat',
            unique_together=set([('row', 'seat')]),
        ),
        migrations.AddField(
            model_name='rebelvoteactivity',
            name='vote',
            field=models.ForeignKey(to='parliament.Vote', unique=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='plenaryvote',
            name='docs',
            field=models.ManyToManyField(to='parliament.Document', through='parliament.PlenaryVoteDocument'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='plenaryvote',
            name='keywords',
            field=models.ManyToManyField(to='parliament.Keyword'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='plenaryvote',
            name='plsess',
            field=models.ForeignKey(to='parliament.PlenarySession'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='plenaryvote',
            name='plsess_item',
            field=models.ForeignKey(related_name='plenary_votes', blank=True, to='parliament.PlenarySessionItem', null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='plenarysessionitemdocument',
            unique_together=set([('item', 'doc')]),
        ),
        migrations.AddField(
            model_name='plenarysessionitem',
            name='docs',
            field=models.ManyToManyField(to='parliament.Document', through='parliament.PlenarySessionItemDocument'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='plenarysessionitem',
            name='plsess',
            field=models.ForeignKey(to='parliament.PlenarySession'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='plenarysessionitem',
            unique_together=set([('plsess', 'number', 'sub_number')]),
        ),
        migrations.AddField(
            model_name='plenarysession',
            name='term',
            field=models.ForeignKey(to='parliament.Term'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='memberseat',
            name='seat',
            field=models.ForeignKey(to='parliament.Seat'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='memberseat',
            unique_together=set([('seat', 'begin', 'end'), ('member', 'begin', 'end')]),
        ),
        migrations.AddField(
            model_name='memberactivity',
            name='member',
            field=models.ForeignKey(to='parliament.Member', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='memberactivity',
            name='type',
            field=models.ForeignKey(to='parliament.MemberActivityType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='member',
            name='party',
            field=models.ForeignKey(blank=True, to='parliament.Party', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='keywordactivityscore',
            name='term',
            field=models.ForeignKey(to='parliament.Term', null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='keywordactivityscore',
            unique_together=set([('keyword', 'term')]),
        ),
        migrations.AddField(
            model_name='keywordactivity',
            name='activity',
            field=models.ForeignKey(to='parliament.MemberActivity'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='keywordactivity',
            name='keyword',
            field=models.ForeignKey(to='parliament.Keyword'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='keywordactivity',
            unique_together=set([('activity', 'keyword')]),
        ),
        migrations.AddField(
            model_name='governingparty',
            name='government',
            field=models.ForeignKey(help_text=b'Government wherein the party participated', to='parliament.Government'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='governingparty',
            name='party',
            field=models.ForeignKey(to='parliament.Party'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='funding',
            name='member',
            field=models.ForeignKey(to='parliament.Member'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='funding',
            name='source',
            field=models.ForeignKey(blank=True, to='parliament.FundingSource', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='funding',
            name='term',
            field=models.ForeignKey(to='parliament.Term'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='funding',
            unique_together=set([('member', 'term', 'type', 'source')]),
        ),
        migrations.AddField(
            model_name='documentsignature',
            name='member',
            field=models.ForeignKey(to='parliament.Member'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='documentsignature',
            unique_together=set([('doc', 'member')]),
        ),
        migrations.AlterUniqueTogether(
            name='documentprocessingstage',
            unique_together=set([('doc', 'index'), ('doc', 'stage')]),
        ),
        migrations.AddField(
            model_name='document',
            name='author',
            field=models.ForeignKey(to='parliament.Member', help_text=b'Set if the document is authored by an MP', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='document',
            name='keywords',
            field=models.ManyToManyField(to='parliament.Keyword'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='document',
            name='related_docs',
            field=models.ManyToManyField(related_name='related_docs_rel_+', to='parliament.Document'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='document',
            unique_together=set([('type', 'name')]),
        ),
        migrations.AddField(
            model_name='districtassociation',
            name='member',
            field=models.ForeignKey(to='parliament.Member'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='districtassociation',
            unique_together=set([('member', 'begin')]),
        ),
        migrations.AddField(
            model_name='committeedissentactivity',
            name='doc',
            field=models.ForeignKey(to='parliament.Document'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='committeeassociation',
            name='member',
            field=models.ForeignKey(to='parliament.Member'),
            preserve_default=True,
        ),
    ]
