# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
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

        # Adding model 'FundingSource'
        db.create_table('parliament_fundingsource', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=120, null=True, blank=True)),
        ))
        db.send_create_signal('parliament', ['FundingSource'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'Funding', fields ['member', 'term', 'type', 'source']
        db.delete_unique('parliament_funding', ['member_id', 'term_id', 'type', 'source_id'])

        # Deleting model 'Funding'
        db.delete_table('parliament_funding')

        # Deleting model 'FundingSource'
        db.delete_table('parliament_fundingsource')


    models = {
        'models.memberactivity': {
            'Meta': {'ordering': "('date', 'member__name')", 'object_name': 'MemberActivity'},
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Member']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '5', 'db_index': 'True'}),
            'weight': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'parliament.committeedissentactivity': {
            'Meta': {'ordering': "('date', 'member__name')", 'object_name': 'CommitteeDissentActivity', '_ormbases': ['models.MemberActivity']},
            'doc': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Document']"}),
            'memberactivity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['models.MemberActivity']", 'unique': 'True', 'primary_key': 'True'})
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
            'Meta': {'ordering': "('date',)", 'unique_together': "(('type', 'id'),)", 'object_name': 'Document'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info_link': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'keywords': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['parliament.Keyword']", 'symmetrical': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20', 'db_index': 'True'}),
            'related_docs': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'related_docs_rel_+'", 'to': "orm['parliament.Document']"}),
            'sgml_link': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'subject': ('django.db.models.fields.TextField', [], {}),
            'summary': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '5', 'db_index': 'True'}),
            'url_name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '20', 'db_index': 'True'})
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
            'Meta': {'ordering': "('date', 'member__name')", 'object_name': 'InitiativeActivity', '_ormbases': ['models.MemberActivity']},
            'doc': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Document']"}),
            'memberactivity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['models.MemberActivity']", 'unique': 'True', 'primary_key': 'True'})
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
            'url_name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'wikipedia_link': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
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
            'url_name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '20', 'db_index': 'True'})
        },
        'parliament.plenarysessionitem': {
            'Meta': {'ordering': "('-plsess__date', '-number', '-sub_number')", 'unique_together': "(('plsess', 'number', 'sub_number'),)", 'object_name': 'PlenarySessionItem'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nr_statements': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'nr_votes': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'number': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'plsess': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.PlenarySession']"}),
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
