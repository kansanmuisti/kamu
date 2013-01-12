# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Keyword'
        db.create_table('parliament_keyword', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=128, db_index=True)),
        ))
        db.send_create_signal('parliament', ['Keyword'])

        # Adding model 'Document'
        db.create_table('parliament_document', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=5, db_index=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=20, db_index=True)),
            ('url_name', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=20)),
            ('date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('info_link', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('sgml_link', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('subject', self.gf('django.db.models.fields.TextField')()),
            ('summary', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('version', self.gf('django.db.models.fields.CharField')(max_length=10, null=True)),
            ('update_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('error', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
        ))
        db.send_create_signal('parliament', ['Document'])

        # Adding unique constraint on 'Document', fields ['type', 'name']
        db.create_unique('parliament_document', ['type', 'name'])

        # Adding M2M table for field related_docs on 'Document'
        db.create_table('parliament_document_related_docs', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_document', models.ForeignKey(orm['parliament.document'], null=False)),
            ('to_document', models.ForeignKey(orm['parliament.document'], null=False))
        ))
        db.create_unique('parliament_document_related_docs', ['from_document_id', 'to_document_id'])

        # Adding M2M table for field keywords on 'Document'
        db.create_table('parliament_document_keywords', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('document', models.ForeignKey(orm['parliament.document'], null=False)),
            ('keyword', models.ForeignKey(orm['parliament.keyword'], null=False))
        ))
        db.create_unique('parliament_document_keywords', ['document_id', 'keyword_id'])

        # Adding model 'Party'
        db.create_table('parliament_party', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=10, db_index=True)),
            ('full_name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('logo', self.gf('django.db.models.fields.files.ImageField')(max_length=100)),
            ('homepage_link', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('vis_color', self.gf('django.db.models.fields.CharField')(max_length=15, null=True, blank=True)),
        ))
        db.send_create_signal('parliament', ['Party'])

        # Adding model 'Term'
        db.create_table('parliament_term', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('display_name', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('begin', self.gf('django.db.models.fields.DateField')()),
            ('end', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('visible', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('parliament', ['Term'])

        # Adding model 'PlenarySession'
        db.create_table('parliament_plenarysession', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('term', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['parliament.Term'])),
            ('date', self.gf('django.db.models.fields.DateField')(db_index=True)),
            ('info_link', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('url_name', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=20)),
            ('origin_id', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=50, null=True, blank=True)),
            ('origin_version', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
            ('import_time', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('parliament', ['PlenarySession'])

        # Adding model 'PlenarySessionItem'
        db.create_table('parliament_plenarysessionitem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('plsess', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['parliament.PlenarySession'])),
            ('number', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('sub_number', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=1000)),
            ('sub_description', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('nr_votes', self.gf('django.db.models.fields.IntegerField')(db_index=True, null=True, blank=True)),
            ('nr_statements', self.gf('django.db.models.fields.IntegerField')(db_index=True, null=True, blank=True)),
        ))
        db.send_create_signal('parliament', ['PlenarySessionItem'])

        # Adding unique constraint on 'PlenarySessionItem', fields ['plsess', 'number', 'sub_number']
        db.create_unique('parliament_plenarysessionitem', ['plsess_id', 'number', 'sub_number'])

        # Adding model 'Statement'
        db.create_table('parliament_statement', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['parliament.PlenarySessionItem'])),
            ('index', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('member', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['parliament.Member'], null=True)),
            ('speaker_name', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('speaker_role', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('text', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('parliament', ['Statement'])

        # Adding unique constraint on 'Statement', fields ['item', 'index']
        db.create_unique('parliament_statement', ['item_id', 'index'])

        # Adding model 'PlenaryVote'
        db.create_table('parliament_plenaryvote', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('plsess', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['parliament.PlenarySession'])),
            ('plsess_item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['parliament.PlenarySessionItem'], null=True, blank=True)),
            ('number', self.gf('django.db.models.fields.IntegerField')()),
            ('time', self.gf('django.db.models.fields.DateTimeField')()),
            ('subject', self.gf('django.db.models.fields.TextField')()),
            ('setting', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('info_link', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('vote_counts', self.gf('django.db.models.fields.CommaSeparatedIntegerField')(max_length=20, null=True, blank=True)),
        ))
        db.send_create_signal('parliament', ['PlenaryVote'])

        # Adding M2M table for field keywords on 'PlenaryVote'
        db.create_table('parliament_plenaryvote_keywords', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('plenaryvote', models.ForeignKey(orm['parliament.plenaryvote'], null=False)),
            ('keyword', models.ForeignKey(orm['parliament.keyword'], null=False))
        ))
        db.create_unique('parliament_plenaryvote_keywords', ['plenaryvote_id', 'keyword_id'])

        # Adding model 'PlenaryVoteDocument'
        db.create_table('parliament_plenaryvotedocument', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('session', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['parliament.PlenaryVote'])),
            ('doc', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['parliament.Document'])),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('parliament', ['PlenaryVoteDocument'])

        # Adding model 'Vote'
        db.create_table('parliament_vote', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('session', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['parliament.PlenaryVote'])),
            ('vote', self.gf('django.db.models.fields.CharField')(max_length=1, db_index=True)),
            ('member', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['parliament.Member'])),
            ('party', self.gf('django.db.models.fields.CharField')(max_length=10)),
        ))
        db.send_create_signal('parliament', ['Vote'])

        # Adding model 'Member'
        db.create_table('parliament_member', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
            ('origin_id', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=20, unique=True, null=True, blank=True)),
            ('url_name', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
            ('birth_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('birth_place', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('given_names', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('surname', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75, null=True, blank=True)),
            ('phone', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('party', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['parliament.Party'], null=True, blank=True)),
            ('photo', self.gf('django.db.models.fields.files.ImageField')(max_length=100)),
            ('info_link', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('wikipedia_link', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('homepage_link', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
        ))
        db.send_create_signal('parliament', ['Member'])

        # Adding model 'MemberStats'
        db.create_table('parliament_memberstats', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('member', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['parliament.Member'])),
            ('begin', self.gf('django.db.models.fields.DateField')()),
            ('end', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('party_agreement', self.gf('django.db.models.fields.CommaSeparatedIntegerField')(max_length=20)),
            ('session_agreement', self.gf('django.db.models.fields.CommaSeparatedIntegerField')(max_length=20)),
            ('vote_counts', self.gf('django.db.models.fields.CommaSeparatedIntegerField')(max_length=30)),
            ('statement_count', self.gf('django.db.models.fields.IntegerField')()),
            ('election_budget', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=2, blank=True)),
        ))
        db.send_create_signal('parliament', ['MemberStats'])

        # Adding model 'TermMember'
        db.create_table('parliament_termmember', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('term', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['parliament.Term'])),
            ('member', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['parliament.Member'])),
            ('election_budget', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=2, blank=True)),
        ))
        db.send_create_signal('parliament', ['TermMember'])

        # Adding model 'Seat'
        db.create_table('parliament_seat', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('row', self.gf('django.db.models.fields.IntegerField')()),
            ('seat', self.gf('django.db.models.fields.IntegerField')()),
            ('x', self.gf('django.db.models.fields.FloatField')()),
            ('y', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal('parliament', ['Seat'])

        # Adding unique constraint on 'Seat', fields ['row', 'seat']
        db.create_unique('parliament_seat', ['row', 'seat'])

        # Adding model 'MemberSeat'
        db.create_table('parliament_memberseat', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('seat', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['parliament.Seat'])),
            ('member', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['parliament.Member'])),
            ('begin', self.gf('django.db.models.fields.DateField')()),
            ('end', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
        ))
        db.send_create_signal('parliament', ['MemberSeat'])

        # Adding unique constraint on 'MemberSeat', fields ['member', 'begin', 'end']
        db.create_unique('parliament_memberseat', ['member_id', 'begin', 'end'])

        # Adding unique constraint on 'MemberSeat', fields ['seat', 'begin', 'end']
        db.create_unique('parliament_memberseat', ['seat_id', 'begin', 'end'])

        # Adding model 'District'
        db.create_table('parliament_district', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, db_index=True)),
            ('long_name', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
        ))
        db.send_create_signal('parliament', ['District'])

        # Adding model 'DistrictAssociation'
        db.create_table('parliament_districtassociation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('member', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['parliament.Member'])),
            ('district', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['parliament.District'], null=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('begin', self.gf('django.db.models.fields.DateField')()),
            ('end', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
        ))
        db.send_create_signal('parliament', ['DistrictAssociation'])

        # Adding unique constraint on 'DistrictAssociation', fields ['member', 'begin']
        db.create_unique('parliament_districtassociation', ['member_id', 'begin'])

        # Adding model 'PartyAssociation'
        db.create_table('parliament_partyassociation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('member', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['parliament.Member'])),
            ('party', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['parliament.Party'], null=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('begin', self.gf('django.db.models.fields.DateField')()),
            ('end', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
        ))
        db.send_create_signal('parliament', ['PartyAssociation'])

        # Adding model 'MemberActivity'
        db.create_table('parliament_memberactivity', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('member', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['parliament.Member'])),
            ('date', self.gf('django.db.models.fields.DateField')(db_index=True)),
            ('weight', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=5, db_index=True)),
        ))
        db.send_create_signal('parliament', ['MemberActivity'])

        # Adding model 'InitiativeActivity'
        db.create_table('parliament_initiativeactivity', (
            ('memberactivity_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['parliament.MemberActivity'], unique=True, primary_key=True)),
            ('doc', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['parliament.Document'])),
        ))
        db.send_create_signal('parliament', ['InitiativeActivity'])

        # Adding model 'CommitteeDissentActivity'
        db.create_table('parliament_committeedissentactivity', (
            ('memberactivity_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['parliament.MemberActivity'], unique=True, primary_key=True)),
            ('doc', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['parliament.Document'])),
        ))
        db.send_create_signal('parliament', ['CommitteeDissentActivity'])

        # Adding model 'MemberSocialFeed'
        db.create_table('parliament_membersocialfeed', (
            ('feed_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['social.Feed'], unique=True, primary_key=True)),
            ('member', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['parliament.Member'])),
        ))
        db.send_create_signal('parliament', ['MemberSocialFeed'])

        # Adding model 'FundingSource'
        db.create_table('parliament_fundingsource', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=120, null=True, blank=True)),
        ))
        db.send_create_signal('parliament', ['FundingSource'])

        # Adding model 'Funding'
        db.create_table('parliament_funding', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=6)),
            ('member', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['parliament.Member'])),
            ('term', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['parliament.Term'])),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['parliament.FundingSource'], null=True, blank=True)),
            ('amount', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=2)),
        ))
        db.send_create_signal('parliament', ['Funding'])

        # Adding unique constraint on 'Funding', fields ['member', 'term', 'type', 'source']
        db.create_unique('parliament_funding', ['member_id', 'term_id', 'type', 'source_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Funding', fields ['member', 'term', 'type', 'source']
        db.delete_unique('parliament_funding', ['member_id', 'term_id', 'type', 'source_id'])

        # Removing unique constraint on 'DistrictAssociation', fields ['member', 'begin']
        db.delete_unique('parliament_districtassociation', ['member_id', 'begin'])

        # Removing unique constraint on 'MemberSeat', fields ['seat', 'begin', 'end']
        db.delete_unique('parliament_memberseat', ['seat_id', 'begin', 'end'])

        # Removing unique constraint on 'MemberSeat', fields ['member', 'begin', 'end']
        db.delete_unique('parliament_memberseat', ['member_id', 'begin', 'end'])

        # Removing unique constraint on 'Seat', fields ['row', 'seat']
        db.delete_unique('parliament_seat', ['row', 'seat'])

        # Removing unique constraint on 'Statement', fields ['item', 'index']
        db.delete_unique('parliament_statement', ['item_id', 'index'])

        # Removing unique constraint on 'PlenarySessionItem', fields ['plsess', 'number', 'sub_number']
        db.delete_unique('parliament_plenarysessionitem', ['plsess_id', 'number', 'sub_number'])

        # Removing unique constraint on 'Document', fields ['type', 'name']
        db.delete_unique('parliament_document', ['type', 'name'])

        # Deleting model 'Keyword'
        db.delete_table('parliament_keyword')

        # Deleting model 'Document'
        db.delete_table('parliament_document')

        # Removing M2M table for field related_docs on 'Document'
        db.delete_table('parliament_document_related_docs')

        # Removing M2M table for field keywords on 'Document'
        db.delete_table('parliament_document_keywords')

        # Deleting model 'Party'
        db.delete_table('parliament_party')

        # Deleting model 'Term'
        db.delete_table('parliament_term')

        # Deleting model 'PlenarySession'
        db.delete_table('parliament_plenarysession')

        # Deleting model 'PlenarySessionItem'
        db.delete_table('parliament_plenarysessionitem')

        # Deleting model 'Statement'
        db.delete_table('parliament_statement')

        # Deleting model 'PlenaryVote'
        db.delete_table('parliament_plenaryvote')

        # Removing M2M table for field keywords on 'PlenaryVote'
        db.delete_table('parliament_plenaryvote_keywords')

        # Deleting model 'PlenaryVoteDocument'
        db.delete_table('parliament_plenaryvotedocument')

        # Deleting model 'Vote'
        db.delete_table('parliament_vote')

        # Deleting model 'Member'
        db.delete_table('parliament_member')

        # Deleting model 'MemberStats'
        db.delete_table('parliament_memberstats')

        # Deleting model 'TermMember'
        db.delete_table('parliament_termmember')

        # Deleting model 'Seat'
        db.delete_table('parliament_seat')

        # Deleting model 'MemberSeat'
        db.delete_table('parliament_memberseat')

        # Deleting model 'District'
        db.delete_table('parliament_district')

        # Deleting model 'DistrictAssociation'
        db.delete_table('parliament_districtassociation')

        # Deleting model 'PartyAssociation'
        db.delete_table('parliament_partyassociation')

        # Deleting model 'MemberActivity'
        db.delete_table('parliament_memberactivity')

        # Deleting model 'InitiativeActivity'
        db.delete_table('parliament_initiativeactivity')

        # Deleting model 'CommitteeDissentActivity'
        db.delete_table('parliament_committeedissentactivity')

        # Deleting model 'MemberSocialFeed'
        db.delete_table('parliament_membersocialfeed')

        # Deleting model 'FundingSource'
        db.delete_table('parliament_fundingsource')

        # Deleting model 'Funding'
        db.delete_table('parliament_funding')


    models = {
        'parliament.committeedissentactivity': {
            'Meta': {'ordering': "('date', 'member__name')", 'object_name': 'CommitteeDissentActivity', '_ormbases': ['parliament.MemberActivity']},
            'doc': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Document']"}),
            'memberactivity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['parliament.MemberActivity']", 'unique': 'True', 'primary_key': 'True'})
        },
        'parliament.district': {
            'Meta': {'object_name': 'District'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'long_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'})
        },
        'parliament.districtassociation': {
            'Meta': {'unique_together': "(('member', 'begin'),)", 'object_name': 'DistrictAssociation'},
            'begin': ('django.db.models.fields.DateField', [], {}),
            'district': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.District']", 'null': 'True'}),
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Member']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'})
        },
        'parliament.document': {
            'Meta': {'ordering': "('date',)", 'unique_together': "(('type', 'name'),)", 'object_name': 'Document'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'error': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info_link': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'keywords': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['parliament.Keyword']", 'symmetrical': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20', 'db_index': 'True'}),
            'related_docs': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'related_docs_rel_+'", 'to': "orm['parliament.Document']"}),
            'sgml_link': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'subject': ('django.db.models.fields.TextField', [], {}),
            'summary': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '5', 'db_index': 'True'}),
            'update_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'url_name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '20'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'})
        },
        'parliament.funding': {
            'Meta': {'unique_together': "(('member', 'term', 'type', 'source'),)", 'object_name': 'Funding'},
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Member']"}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.FundingSource']", 'null': 'True', 'blank': 'True'}),
            'term': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Term']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '6'})
        },
        'parliament.fundingsource': {
            'Meta': {'object_name': 'FundingSource'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'})
        },
        'parliament.initiativeactivity': {
            'Meta': {'ordering': "('date', 'member__name')", 'object_name': 'InitiativeActivity', '_ormbases': ['parliament.MemberActivity']},
            'doc': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Document']"}),
            'memberactivity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['parliament.MemberActivity']", 'unique': 'True', 'primary_key': 'True'})
        },
        'parliament.keyword': {
            'Meta': {'object_name': 'Keyword'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128', 'db_index': 'True'})
        },
        'parliament.member': {
            'Meta': {'object_name': 'Member'},
            'birth_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'birth_place': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'given_names': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'homepage_link': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info_link': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'origin_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '20', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Party']", 'null': 'True', 'blank': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'photo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'surname': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'url_name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'wikipedia_link': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        'parliament.memberactivity': {
            'Meta': {'ordering': "('date', 'member__name')", 'object_name': 'MemberActivity'},
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Member']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '5', 'db_index': 'True'}),
            'weight': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'parliament.memberseat': {
            'Meta': {'unique_together': "(('member', 'begin', 'end'), ('seat', 'begin', 'end'))", 'object_name': 'MemberSeat'},
            'begin': ('django.db.models.fields.DateField', [], {}),
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Member']"}),
            'seat': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Seat']"})
        },
        'parliament.membersocialfeed': {
            'Meta': {'object_name': 'MemberSocialFeed', '_ormbases': ['social.Feed']},
            'feed_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['social.Feed']", 'unique': 'True', 'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Member']"})
        },
        'parliament.memberstats': {
            'Meta': {'object_name': 'MemberStats'},
            'begin': ('django.db.models.fields.DateField', [], {}),
            'election_budget': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Member']"}),
            'party_agreement': ('django.db.models.fields.CommaSeparatedIntegerField', [], {'max_length': '20'}),
            'session_agreement': ('django.db.models.fields.CommaSeparatedIntegerField', [], {'max_length': '20'}),
            'statement_count': ('django.db.models.fields.IntegerField', [], {}),
            'vote_counts': ('django.db.models.fields.CommaSeparatedIntegerField', [], {'max_length': '30'})
        },
        'parliament.party': {
            'Meta': {'object_name': 'Party'},
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'homepage_link': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'logo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10', 'db_index': 'True'}),
            'vis_color': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'})
        },
        'parliament.partyassociation': {
            'Meta': {'object_name': 'PartyAssociation'},
            'begin': ('django.db.models.fields.DateField', [], {}),
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Member']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Party']", 'null': 'True'})
        },
        'parliament.plenarysession': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'PlenarySession'},
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'import_time': ('django.db.models.fields.DateTimeField', [], {}),
            'info_link': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'origin_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'origin_version': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'term': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Term']"}),
            'url_name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '20'})
        },
        'parliament.plenarysessionitem': {
            'Meta': {'ordering': "('-plsess__date', '-number', '-sub_number')", 'unique_together': "(('plsess', 'number', 'sub_number'),)", 'object_name': 'PlenarySessionItem'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nr_statements': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'nr_votes': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'number': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'plsess': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.PlenarySession']"}),
            'sub_description': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'sub_number': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '15'})
        },
        'parliament.plenaryvote': {
            'Meta': {'ordering': "('plsess__date', 'number')", 'object_name': 'PlenaryVote'},
            'docs': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['parliament.Document']", 'through': "orm['parliament.PlenaryVoteDocument']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info_link': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'keywords': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['parliament.Keyword']", 'symmetrical': 'False'}),
            'number': ('django.db.models.fields.IntegerField', [], {}),
            'plsess': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.PlenarySession']"}),
            'plsess_item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.PlenarySessionItem']", 'null': 'True', 'blank': 'True'}),
            'setting': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'subject': ('django.db.models.fields.TextField', [], {}),
            'time': ('django.db.models.fields.DateTimeField', [], {}),
            'vote_counts': ('django.db.models.fields.CommaSeparatedIntegerField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'})
        },
        'parliament.plenaryvotedocument': {
            'Meta': {'object_name': 'PlenaryVoteDocument'},
            'doc': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Document']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.PlenaryVote']"})
        },
        'parliament.seat': {
            'Meta': {'unique_together': "(('row', 'seat'),)", 'object_name': 'Seat'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'row': ('django.db.models.fields.IntegerField', [], {}),
            'seat': ('django.db.models.fields.IntegerField', [], {}),
            'x': ('django.db.models.fields.FloatField', [], {}),
            'y': ('django.db.models.fields.FloatField', [], {})
        },
        'parliament.statement': {
            'Meta': {'ordering': "('item', 'index')", 'unique_together': "(('item', 'index'),)", 'object_name': 'Statement'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.PlenarySessionItem']"}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Member']", 'null': 'True'}),
            'speaker_name': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'speaker_role': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        'parliament.term': {
            'Meta': {'ordering': "('-begin',)", 'object_name': 'Term'},
            'begin': ('django.db.models.fields.DateField', [], {}),
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'parliament.termmember': {
            'Meta': {'object_name': 'TermMember'},
            'election_budget': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Member']"}),
            'term': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Term']"})
        },
        'parliament.vote': {
            'Meta': {'object_name': 'Vote'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Member']"}),
            'party': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.PlenaryVote']"}),
            'vote': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'})
        },
        'social.feed': {
            'Meta': {'unique_together': "(('type', 'origin_id'),)", 'object_name': 'Feed'},
            'account_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_update': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'origin_id': ('django.db.models.fields.CharField', [], {'max_length': '25', 'db_index': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'update_error_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        }
    }

    complete_apps = ['parliament']