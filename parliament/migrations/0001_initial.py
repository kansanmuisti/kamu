# Generated by Django 2.2.9 on 2019-12-21 15:58

from django.db import migrations, models
import django.db.models.deletion
import sortedm2m.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('social', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Committee',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_modified_time', models.DateTimeField(null=True)),
                ('last_checked_time', models.DateTimeField(null=True)),
                ('name', models.CharField(help_text='Name of the committee', max_length=100, unique=True)),
                ('description', models.CharField(help_text='Description of the committee', max_length=500, null=True)),
                ('origin_id', models.CharField(help_text='Upstream identifier (in URL)', max_length=20, null=True, unique=True)),
                ('current', models.BooleanField(default=True, help_text='Is the committee current or past')),
                ('url_name', models.CharField(help_text='Name identifier for URLs', max_length=100, null=True, unique=True)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='District',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=50)),
                ('long_name', models.CharField(blank=True, max_length=50, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_modified_time', models.DateTimeField(null=True)),
                ('last_checked_time', models.DateTimeField(null=True)),
                ('type', models.CharField(choices=[('mp_prop', 'MP law proposal'), ('gov_bill', 'Government bill'), ('written_ques', 'Written question'), ('interpellation', 'Interpellation')], db_index=True, max_length=30)),
                ('name', models.CharField(db_index=True, max_length=30, unique=True)),
                ('origin_id', models.CharField(db_index=True, max_length=30, unique=True)),
                ('url_name', models.SlugField(max_length=20, unique=True)),
                ('date', models.DateField(blank=True, null=True)),
                ('info_link', models.URLField(blank=True, null=True)),
                ('sgml_link', models.URLField(blank=True, null=True)),
                ('subject', models.TextField()),
                ('summary', models.TextField(blank=True, null=True)),
                ('question', models.TextField(blank=True, null=True)),
                ('answer', models.TextField(blank=True, null=True)),
                ('answerer_name', models.CharField(blank=True, max_length=50, null=True)),
                ('answerer_title', models.CharField(blank=True, max_length=50, null=True)),
                ('version', models.CharField(max_length=10, null=True)),
                ('error', models.CharField(blank=True, max_length=50, null=True)),
            ],
            options={
                'ordering': ('date',),
            },
        ),
        migrations.CreateModel(
            name='FundingSource',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=120, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Government',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('begin', models.DateField(help_text='Date when the government began operations')),
                ('end', models.DateField(help_text='End date for the government', null=True)),
                ('name', models.CharField(help_text='Descriptive name for this government, depends on national custom', max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Keyword',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=128, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Member',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_modified_time', models.DateTimeField(null=True)),
                ('last_checked_time', models.DateTimeField(null=True)),
                ('name', models.CharField(max_length=50, unique=True)),
                ('origin_id', models.CharField(blank=True, db_index=True, max_length=20, null=True, unique=True)),
                ('url_name', models.SlugField(unique=True)),
                ('birth_date', models.DateField(blank=True, null=True)),
                ('birth_place', models.CharField(blank=True, max_length=50, null=True)),
                ('given_names', models.CharField(max_length=50)),
                ('gender', models.CharField(blank=True, max_length=1, null=True)),
                ('surname', models.CharField(max_length=50)),
                ('summary', models.TextField(null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('phone', models.CharField(blank=True, max_length=20, null=True)),
                ('photo', models.ImageField(upload_to='images/members')),
                ('info_link', models.URLField()),
                ('wikipedia_link', models.URLField(blank=True, null=True)),
                ('homepage_link', models.URLField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='MemberActivityType',
            fields=[
                ('type', models.CharField(max_length=5, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('weight', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='Party',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_modified_time', models.DateTimeField(null=True)),
                ('last_checked_time', models.DateTimeField(null=True)),
                ('abbreviation', models.CharField(db_index=True, max_length=10, unique=True)),
                ('name', models.CharField(max_length=50)),
                ('logo', models.ImageField(upload_to='images/parties')),
                ('homepage_link', models.URLField()),
                ('vis_color', models.CharField(blank=True, max_length=15, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='PlenarySession',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_modified_time', models.DateTimeField(null=True)),
                ('last_checked_time', models.DateTimeField(null=True)),
                ('name', models.CharField(max_length=20)),
                ('date', models.DateField(db_index=True)),
                ('info_link', models.URLField()),
                ('url_name', models.SlugField(max_length=20, unique=True)),
                ('origin_id', models.CharField(blank=True, db_index=True, max_length=50, null=True)),
                ('origin_version', models.CharField(blank=True, max_length=10, null=True)),
            ],
            options={
                'ordering': ('-date',),
            },
        ),
        migrations.CreateModel(
            name='PlenarySessionItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.PositiveIntegerField()),
                ('sub_number', models.PositiveIntegerField(blank=True, null=True)),
                ('type', models.CharField(choices=[('agenda', 'Agenda item'), ('question', 'Question time'), ('budget', 'Budget proposal')], max_length=15)),
                ('description', models.CharField(max_length=1000)),
                ('sub_description', models.CharField(blank=True, max_length=100, null=True)),
                ('processing_stage', models.CharField(blank=True, db_index=True, max_length=20, null=True)),
                ('nr_votes', models.IntegerField(blank=True, db_index=True, null=True)),
                ('nr_statements', models.IntegerField(blank=True, db_index=True, null=True)),
            ],
            options={
                'ordering': ('-plsess__date', '-number', '-sub_number'),
            },
        ),
        migrations.CreateModel(
            name='PlenaryVote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_modified_time', models.DateTimeField(null=True)),
                ('last_checked_time', models.DateTimeField(null=True)),
                ('number', models.IntegerField()),
                ('time', models.DateTimeField()),
                ('subject', models.TextField()),
                ('setting', models.CharField(max_length=200)),
                ('info_link', models.URLField(blank=True, null=True)),
                ('vote_counts', models.CharField(blank=True, max_length=20, null=True)),
            ],
            options={
                'ordering': ('plsess__date', 'number'),
            },
        ),
        migrations.CreateModel(
            name='Term',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=40)),
                ('display_name', models.CharField(max_length=40)),
                ('begin', models.DateField()),
                ('end', models.DateField(blank=True, null=True)),
                ('visible', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ('-begin',),
            },
        ),
        migrations.CreateModel(
            name='TermMember',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('election_budget', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.Member')),
                ('term', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.Term')),
            ],
        ),
        migrations.CreateModel(
            name='Statement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('index', models.PositiveIntegerField(db_index=True)),
                ('speaker_name', models.CharField(blank=True, max_length=40, null=True)),
                ('speaker_role', models.CharField(blank=True, max_length=40, null=True)),
                ('type', models.CharField(choices=[('normal', 'Statement'), ('speaker', 'Speaker statement')], max_length=15)),
                ('text', models.TextField()),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.PlenarySessionItem')),
                ('member', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='parliament.Member')),
            ],
            options={
                'ordering': ('item', 'index'),
                'unique_together': {('item', 'index')},
            },
        ),
        migrations.CreateModel(
            name='SpeakerAssociation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('begin', models.DateField()),
                ('end', models.DateField(blank=True, db_index=True, null=True)),
                ('role', models.CharField(choices=[('speaker', 'Speaker'), ('1st-deputy-speaker', '1st Deputy Speaker'), ('2nd-deputy-speaker', '2st Deputy Speaker')], help_text='Speaker position', max_length=20)),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.Member')),
            ],
        ),
        migrations.CreateModel(
            name='Seat',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('row', models.IntegerField()),
                ('seat', models.IntegerField()),
                ('x', models.FloatField()),
                ('y', models.FloatField()),
            ],
            options={
                'unique_together': {('row', 'seat')},
            },
        ),
        migrations.CreateModel(
            name='PlenaryVoteDocument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveIntegerField()),
                ('doc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.Document')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.PlenaryVote')),
            ],
        ),
        migrations.AddField(
            model_name='plenaryvote',
            name='docs',
            field=models.ManyToManyField(through='parliament.PlenaryVoteDocument', to='parliament.Document'),
        ),
        migrations.AddField(
            model_name='plenaryvote',
            name='keywords',
            field=models.ManyToManyField(to='parliament.Keyword'),
        ),
        migrations.AddField(
            model_name='plenaryvote',
            name='plsess',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.PlenarySession'),
        ),
        migrations.AddField(
            model_name='plenaryvote',
            name='plsess_item',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='plenary_votes', to='parliament.PlenarySessionItem'),
        ),
        migrations.CreateModel(
            name='PlenarySessionItemDocument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveIntegerField()),
                ('stage', models.CharField(blank=True, max_length=50, null=True)),
                ('doc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.Document')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.PlenarySessionItem')),
            ],
            options={
                'ordering': ('order',),
                'unique_together': {('item', 'doc')},
            },
        ),
        migrations.AddField(
            model_name='plenarysessionitem',
            name='docs',
            field=models.ManyToManyField(through='parliament.PlenarySessionItemDocument', to='parliament.Document'),
        ),
        migrations.AddField(
            model_name='plenarysessionitem',
            name='plsess',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.PlenarySession'),
        ),
        migrations.AddField(
            model_name='plenarysession',
            name='term',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.Term'),
        ),
        migrations.CreateModel(
            name='PartyAssociation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=50, null=True)),
                ('begin', models.DateField()),
                ('end', models.DateField(blank=True, null=True)),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.Member')),
                ('party', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='parliament.Party')),
            ],
        ),
        migrations.CreateModel(
            name='MinistryAssociation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('begin', models.DateField()),
                ('end', models.DateField(blank=True, db_index=True, null=True)),
                ('label', models.CharField(help_text='Official descriptive name of the position. eg. minister of of International Development', max_length=50)),
                ('role', models.CharField(choices=[('minister', 'Minister')], help_text='Position of the official. eg. minister.', max_length=20)),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.Member')),
            ],
        ),
        migrations.CreateModel(
            name='MemberStats',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('begin', models.DateField()),
                ('end', models.DateField(blank=True, null=True)),
                ('party_agreement', models.CharField(max_length=20)),
                ('session_agreement', models.CharField(max_length=20)),
                ('vote_counts', models.CharField(max_length=30)),
                ('statement_count', models.IntegerField()),
                ('election_budget', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.Member')),
            ],
        ),
        migrations.CreateModel(
            name='MemberSocialFeed',
            fields=[
                ('feed_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='social.Feed')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.Member')),
            ],
            bases=('social.feed',),
        ),
        migrations.CreateModel(
            name='MemberActivity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', models.DateTimeField(db_index=True)),
                ('last_modified_time', models.DateTimeField(null=True)),
                ('member', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='parliament.Member')),
                ('type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.MemberActivityType')),
            ],
            options={
                'ordering': ('time', 'member__name'),
                'index_together': {('member', 'time')},
            },
        ),
        migrations.AddField(
            model_name='member',
            name='party',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='parliament.Party'),
        ),
        migrations.CreateModel(
            name='GoverningParty',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('begin', models.DateField(help_text='Beginning of government participation')),
                ('end', models.DateField(help_text='End of government participation', null=True)),
                ('government', models.ForeignKey(help_text='Government wherein the party participated', on_delete=django.db.models.deletion.CASCADE, to='parliament.Government')),
                ('party', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.Party')),
            ],
        ),
        migrations.CreateModel(
            name='DocumentSignature',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('doc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.Document')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.Member')),
            ],
            options={
                'unique_together': {('doc', 'member')},
            },
        ),
        migrations.AddField(
            model_name='document',
            name='author',
            field=models.ForeignKey(help_text='Set if the document is authored by an MP', null=True, on_delete=django.db.models.deletion.CASCADE, to='parliament.Member'),
        ),
        migrations.AddField(
            model_name='document',
            name='keywords',
            field=sortedm2m.fields.SortedManyToManyField(help_text=None, to='parliament.Keyword'),
        ),
        migrations.AddField(
            model_name='document',
            name='related_docs',
            field=models.ManyToManyField(related_name='_document_related_docs_+', to='parliament.Document'),
        ),
        migrations.CreateModel(
            name='CommitteeAssociation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('begin', models.DateField()),
                ('end', models.DateField(blank=True, db_index=True, null=True)),
                ('role', models.CharField(choices=[('chairman', 'Chairman'), ('deputy-cm', 'Deputy Chairman'), ('member', 'Member'), ('deputy-m', 'Deputy Member')], max_length=15, null=True)),
                ('committee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.Committee')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.Member')),
            ],
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vote', models.CharField(choices=[('Y', 'Yes'), ('N', 'No'), ('A', 'Absent'), ('E', 'Empty'), ('S', 'Speaker')], max_length=1)),
                ('party', models.CharField(max_length=10)),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.Member')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.PlenaryVote')),
            ],
            options={
                'index_together': {('session', 'vote')},
            },
        ),
        migrations.CreateModel(
            name='StatementActivity',
            fields=[
                ('memberactivity_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='parliament.MemberActivity')),
                ('statement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.Statement', unique=True)),
            ],
            bases=('parliament.memberactivity',),
        ),
        migrations.CreateModel(
            name='SocialUpdateActivity',
            fields=[
                ('memberactivity_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='parliament.MemberActivity')),
                ('update', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='social.Update', unique=True)),
            ],
            bases=('parliament.memberactivity',),
        ),
        migrations.CreateModel(
            name='SignatureActivity',
            fields=[
                ('memberactivity_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='parliament.MemberActivity')),
                ('signature', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.DocumentSignature', unique=True)),
            ],
            bases=('parliament.memberactivity',),
        ),
        migrations.CreateModel(
            name='RebelVoteActivity',
            fields=[
                ('memberactivity_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='parliament.MemberActivity')),
                ('vote', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.Vote', unique=True)),
            ],
            bases=('parliament.memberactivity',),
        ),
        migrations.AlterUniqueTogether(
            name='plenarysessionitem',
            unique_together={('plsess', 'number', 'sub_number')},
        ),
        migrations.CreateModel(
            name='MemberSeat',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('begin', models.DateField()),
                ('end', models.DateField(blank=True, null=True)),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.Member')),
                ('seat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.Seat')),
            ],
            options={
                'unique_together': {('member', 'begin', 'end'), ('seat', 'begin', 'end')},
            },
        ),
        migrations.CreateModel(
            name='KeywordActivityScore',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.PositiveIntegerField()),
                ('calc_time', models.DateTimeField(auto_now=True)),
                ('keyword', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.Keyword')),
                ('term', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='parliament.Term')),
            ],
            options={
                'unique_together': {('keyword', 'term')},
            },
        ),
        migrations.CreateModel(
            name='KeywordActivity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('activity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.MemberActivity')),
                ('keyword', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.Keyword')),
            ],
            options={
                'unique_together': {('activity', 'keyword')},
            },
        ),
        migrations.CreateModel(
            name='InitiativeActivity',
            fields=[
                ('memberactivity_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='parliament.MemberActivity')),
                ('doc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.Document')),
            ],
            bases=('parliament.memberactivity',),
        ),
        migrations.CreateModel(
            name='Funding',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('own', 'Own funds'), ('co', 'Corporation'), ('ind', 'Individual'), ('loan', 'Loan'), ('u_ind', 'Undefined individuals'), ('u_com', 'Undefined communities'), ('party', 'Party'), ('oth', 'Other')], max_length=6)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.Member')),
                ('source', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='parliament.FundingSource')),
                ('term', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.Term')),
            ],
            options={
                'unique_together': {('member', 'term', 'type', 'source')},
            },
        ),
        migrations.CreateModel(
            name='DocumentProcessingStage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('index', models.PositiveSmallIntegerField()),
                ('stage', models.CharField(choices=[('intro', 'Introduced'), ('debate', 'Debate'), ('committee', 'In committee'), ('agenda', 'On agenda'), ('1stread', 'First reading'), ('2ndread', 'Second reading'), ('3rdread', 'Third reading'), ('finished', 'Finished'), ('onlyread', 'Only reading'), ('only2read', 'Only and 2nd reading'), ('only3read', 'Only and 3rd reading'), ('cancelled', 'Cancelled'), ('lapsed', 'Lapsed'), ('suspended', 'Suspended'), ('ministry', 'In ministry')], db_index=True, max_length=15)),
                ('date', models.DateField()),
                ('doc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.Document')),
            ],
            options={
                'ordering': ('doc', 'index'),
                'unique_together': {('doc', 'index'), ('doc', 'stage')},
            },
        ),
        migrations.AlterUniqueTogether(
            name='document',
            unique_together={('type', 'name')},
        ),
        migrations.CreateModel(
            name='DistrictAssociation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=50, null=True)),
                ('begin', models.DateField()),
                ('end', models.DateField(blank=True, null=True)),
                ('district', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='parliament.District')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.Member')),
            ],
            options={
                'unique_together': {('member', 'begin')},
            },
        ),
        migrations.CreateModel(
            name='CommitteeDissentActivity',
            fields=[
                ('memberactivity_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='parliament.MemberActivity')),
                ('doc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.Document')),
            ],
            bases=('parliament.memberactivity',),
        ),
    ]
