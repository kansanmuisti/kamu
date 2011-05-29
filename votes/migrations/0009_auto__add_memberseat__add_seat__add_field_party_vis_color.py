# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'MemberSeat'
        db.create_table('votes_memberseat', (
            ('member', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['votes.Member'])),
            ('begin', self.gf('django.db.models.fields.DateField')()),
            ('end', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('seat', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['votes.Seat'])),
        ))
        db.send_create_signal('votes', ['MemberSeat'])

        # Adding model 'Seat'
        db.create_table('votes_seat', (
            ('y', self.gf('django.db.models.fields.FloatField')()),
            ('x', self.gf('django.db.models.fields.FloatField')()),
            ('seat', self.gf('django.db.models.fields.IntegerField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('row', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('votes', ['Seat'])

        # Adding field 'Party.vis_color'
        db.add_column('votes_party', 'vis_color', self.gf('django.db.models.fields.CharField')(max_length=15, null=True, blank=True), keep_default=False)
    
    
    def backwards(self, orm):
        
        # Deleting model 'MemberSeat'
        db.delete_table('votes_memberseat')

        # Deleting model 'Seat'
        db.delete_table('votes_seat')

        # Deleting field 'Party.vis_color'
        db.delete_column('votes_party', 'vis_color')
    
    
    models = {
        'votes.committeedissentactivity': {
            'Meta': {'object_name': 'CommitteeDissentActivity', '_ormbases': ['votes.MemberActivity']},
            'doc': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['votes.Document']"}),
            'memberactivity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['votes.MemberActivity']", 'unique': 'True', 'primary_key': 'True'})
        },
        'votes.county': {
            'Meta': {'object_name': 'County'},
            'district': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'votes.districtassociation': {
            'Meta': {'object_name': 'DistrictAssociation'},
            'begin': ('django.db.models.fields.DateField', [], {}),
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['votes.Member']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'votes.document': {
            'Meta': {'unique_together': "(('type', 'id'),)", 'object_name': 'Document'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info_link': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'keywords': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['votes.Keyword']", 'symmetrical': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20', 'db_index': 'True'}),
            'related_docs': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'related_docs_rel_+'", 'to': "orm['votes.Document']"}),
            'sgml_link': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'subject': ('django.db.models.fields.TextField', [], {}),
            'summary': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '5', 'db_index': 'True'}),
            'url_name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '20', 'db_index': 'True'})
        },
        'votes.initiativeactivity': {
            'Meta': {'object_name': 'InitiativeActivity', '_ormbases': ['votes.MemberActivity']},
            'doc': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['votes.Document']"}),
            'memberactivity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['votes.MemberActivity']", 'unique': 'True', 'primary_key': 'True'})
        },
        'votes.keyword': {
            'Meta': {'object_name': 'Keyword'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128', 'db_index': 'True'})
        },
        'votes.member': {
            'Meta': {'object_name': 'Member'},
            'birth_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'given_names': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'homepage_link': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info_link': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['votes.Party']", 'null': 'True', 'blank': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'photo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'surname': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'twitter_account': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'url_name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'wikipedia_link': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        'votes.memberactivity': {
            'Meta': {'object_name': 'MemberActivity'},
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['votes.Member']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '5', 'db_index': 'True'}),
            'weight': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'votes.memberseat': {
            'Meta': {'unique_together': "(('member', 'begin', 'end'), ('seat', 'begin', 'end'))", 'object_name': 'MemberSeat'},
            'begin': ('django.db.models.fields.DateField', [], {}),
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['votes.Member']"}),
            'seat': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['votes.Seat']"})
        },
        'votes.memberstats': {
            'Meta': {'object_name': 'MemberStats'},
            'begin': ('django.db.models.fields.DateField', [], {}),
            'election_budget': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['votes.Member']"}),
            'party_agreement': ('django.db.models.fields.CommaSeparatedIntegerField', [], {'max_length': '20'}),
            'session_agreement': ('django.db.models.fields.CommaSeparatedIntegerField', [], {'max_length': '20'}),
            'statement_count': ('django.db.models.fields.IntegerField', [], {}),
            'vote_counts': ('django.db.models.fields.CommaSeparatedIntegerField', [], {'max_length': '30'})
        },
        'votes.minutes': {
            'Meta': {'object_name': 'Minutes'},
            'html': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'plenary_session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['votes.PlenarySession']", 'unique': 'True'})
        },
        'votes.party': {
            'Meta': {'object_name': 'Party'},
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'info_link': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'logo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '10', 'primary_key': 'True'}),
            'vis_color': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'})
        },
        'votes.partyassociation': {
            'Meta': {'object_name': 'PartyAssociation'},
            'begin': ('django.db.models.fields.DateField', [], {}),
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['votes.Member']"}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['votes.Party']"})
        },
        'votes.plenarysession': {
            'Meta': {'object_name': 'PlenarySession'},
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'info_link': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20', 'primary_key': 'True'}),
            'term': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['votes.Term']"}),
            'url_name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '20', 'db_index': 'True'})
        },
        'votes.seat': {
            'Meta': {'unique_together': "(('row', 'seat'),)", 'object_name': 'Seat'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'row': ('django.db.models.fields.IntegerField', [], {}),
            'seat': ('django.db.models.fields.IntegerField', [], {}),
            'x': ('django.db.models.fields.FloatField', [], {}),
            'y': ('django.db.models.fields.FloatField', [], {})
        },
        'votes.session': {
            'Meta': {'object_name': 'Session'},
            'docs': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['votes.Document']", 'through': "orm['votes.SessionDocument']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info': ('django.db.models.fields.TextField', [], {}),
            'info_link': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'keywords': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['votes.Keyword']", 'symmetrical': 'False'}),
            'number': ('django.db.models.fields.IntegerField', [], {}),
            'plenary_session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['votes.PlenarySession']"}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'time': ('django.db.models.fields.TimeField', [], {}),
            'vote_counts': ('django.db.models.fields.CommaSeparatedIntegerField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'})
        },
        'votes.sessiondocument': {
            'Meta': {'object_name': 'SessionDocument'},
            'doc': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['votes.Document']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['votes.Session']"})
        },
        'votes.statement': {
            'Meta': {'unique_together': "(('plenary_session', 'dsc_number', 'index'),)", 'object_name': 'Statement'},
            'dsc_number': ('django.db.models.fields.IntegerField', [], {}),
            'html': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index': ('django.db.models.fields.IntegerField', [], {}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['votes.Member']", 'null': 'True', 'blank': 'True'}),
            'plenary_session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['votes.PlenarySession']"}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        'votes.term': {
            'Meta': {'object_name': 'Term'},
            'begin': ('django.db.models.fields.DateField', [], {}),
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'})
        },
        'votes.termmember': {
            'Meta': {'object_name': 'TermMember'},
            'election_budget': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['votes.Member']"}),
            'term': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['votes.Term']"})
        },
        'votes.vote': {
            'Meta': {'object_name': 'Vote'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['votes.Member']"}),
            'party': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['votes.Session']"}),
            'vote': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'})
        }
    }
    
    complete_apps = ['votes']
