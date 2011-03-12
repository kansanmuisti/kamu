# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'Term'
        db.create_table('votes_term', (
            ('end', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('begin', self.gf('django.db.models.fields.DateField')()),
            ('display_name', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=40)),
        ))
        db.send_create_signal('votes', ['Term'])

        # Adding model 'Party'
        db.create_table('votes_party', (
            ('logo', self.gf('django.db.models.fields.files.ImageField')(max_length=100)),
            ('info_link', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=10, primary_key=True)),
            ('full_name', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('votes', ['Party'])

        # Adding model 'Member'
        db.create_table('votes_member', (
            ('twitter_account', self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True)),
            ('url_name', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50, db_index=True)),
            ('surname', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('given_names', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('info_link', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('photo', self.gf('django.db.models.fields.files.ImageField')(max_length=100)),
            ('wikipedia_link', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('phone', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('homepage_link', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('birth_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('party', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['votes.Party'], null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
        ))
        db.send_create_signal('votes', ['Member'])

        # Adding model 'MemberStats'
        db.create_table('votes_memberstats', (
            ('vote_counts', self.gf('django.db.models.fields.CommaSeparatedIntegerField')(max_length=30)),
            ('begin', self.gf('django.db.models.fields.DateField')()),
            ('end', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('session_agreement', self.gf('django.db.models.fields.CommaSeparatedIntegerField')(max_length=20)),
            ('member', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['votes.Member'])),
            ('statement_count', self.gf('django.db.models.fields.IntegerField')()),
            ('election_budget', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=2, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('party_agreement', self.gf('django.db.models.fields.CommaSeparatedIntegerField')(max_length=20)),
        ))
        db.send_create_signal('votes', ['MemberStats'])

        # Adding model 'TermMember'
        db.create_table('votes_termmember', (
            ('member', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['votes.Member'])),
            ('term', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['votes.Term'])),
            ('election_budget', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=2, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('votes', ['TermMember'])

        # Adding model 'DistrictAssociation'
        db.create_table('votes_districtassociation', (
            ('member', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['votes.Member'])),
            ('begin', self.gf('django.db.models.fields.DateField')()),
            ('end', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('votes', ['DistrictAssociation'])

        # Adding model 'County'
        db.create_table('votes_county', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('district', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('votes', ['County'])

        # Adding model 'PartyAssociation'
        db.create_table('votes_partyassociation', (
            ('member', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['votes.Member'])),
            ('party', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['votes.Party'])),
            ('begin', self.gf('django.db.models.fields.DateField')()),
            ('end', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('votes', ['PartyAssociation'])

        # Adding model 'PlenarySession'
        db.create_table('votes_plenarysession', (
            ('date', self.gf('django.db.models.fields.DateField')(db_index=True)),
            ('url_name', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=20, db_index=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=20, primary_key=True)),
            ('info_link', self.gf('django.db.models.fields.URLField')(max_length=200)),
        ))
        db.send_create_signal('votes', ['PlenarySession'])

        # Adding model 'Minutes'
        db.create_table('votes_minutes', (
            ('html', self.gf('django.db.models.fields.TextField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('plenary_session', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['votes.PlenarySession'], unique=True)),
        ))
        db.send_create_signal('votes', ['Minutes'])

        # Adding model 'Statement'
        db.create_table('votes_statement', (
            ('dsc_number', self.gf('django.db.models.fields.IntegerField')()),
            ('index', self.gf('django.db.models.fields.IntegerField')()),
            ('plenary_session', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['votes.PlenarySession'])),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('member', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['votes.Member'], null=True, blank=True)),
            ('html', self.gf('django.db.models.fields.TextField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('votes', ['Statement'])

        # Adding unique constraint on 'Statement', fields ['plenary_session', 'dsc_number', 'index']
        db.create_unique('votes_statement', ['plenary_session_id', 'dsc_number', 'index'])

        # Adding model 'Session'
        db.create_table('votes_session', (
            ('info', self.gf('django.db.models.fields.TextField')()),
            ('info_link', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('plenary_session', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['votes.PlenarySession'])),
            ('number', self.gf('django.db.models.fields.IntegerField')()),
            ('vote_counts', self.gf('django.db.models.fields.CommaSeparatedIntegerField')(max_length=20, null=True, blank=True)),
            ('time', self.gf('django.db.models.fields.TimeField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('subject', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('votes', ['Session'])

        # Adding model 'SessionDocument'
        db.create_table('votes_sessiondocument', (
            ('url_name', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=20, db_index=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('info_link', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=20, db_index=True)),
        ))
        db.send_create_signal('votes', ['SessionDocument'])

        # Adding M2M table for field sessions on 'SessionDocument'
        db.create_table('votes_sessiondocument_sessions', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('sessiondocument', models.ForeignKey(orm['votes.sessiondocument'], null=False)),
            ('session', models.ForeignKey(orm['votes.session'], null=False))
        ))
        db.create_unique('votes_sessiondocument_sessions', ['sessiondocument_id', 'session_id'])

        # Adding model 'Vote'
        db.create_table('votes_vote', (
            ('vote', self.gf('django.db.models.fields.CharField')(max_length=1, db_index=True)),
            ('member', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['votes.Member'])),
            ('session', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['votes.Session'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('party', self.gf('django.db.models.fields.CharField')(max_length=10)),
        ))
        db.send_create_signal('votes', ['Vote'])

        # Adding model 'Keyword'
        db.create_table('votes_keyword', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=128, db_index=True)),
        ))
        db.send_create_signal('votes', ['Keyword'])

        # Adding model 'SessionKeyword'
        db.create_table('votes_sessionkeyword', (
            ('session', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['votes.Session'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('keyword', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['votes.Keyword'])),
        ))
        db.send_create_signal('votes', ['SessionKeyword'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'Term'
        db.delete_table('votes_term')

        # Deleting model 'Party'
        db.delete_table('votes_party')

        # Deleting model 'Member'
        db.delete_table('votes_member')

        # Deleting model 'MemberStats'
        db.delete_table('votes_memberstats')

        # Deleting model 'TermMember'
        db.delete_table('votes_termmember')

        # Deleting model 'DistrictAssociation'
        db.delete_table('votes_districtassociation')

        # Deleting model 'County'
        db.delete_table('votes_county')

        # Deleting model 'PartyAssociation'
        db.delete_table('votes_partyassociation')

        # Deleting model 'PlenarySession'
        db.delete_table('votes_plenarysession')

        # Deleting model 'Minutes'
        db.delete_table('votes_minutes')

        # Deleting model 'Statement'
        db.delete_table('votes_statement')

        # Removing unique constraint on 'Statement', fields ['plenary_session', 'dsc_number', 'index']
        db.delete_unique('votes_statement', ['plenary_session_id', 'dsc_number', 'index'])

        # Deleting model 'Session'
        db.delete_table('votes_session')

        # Deleting model 'SessionDocument'
        db.delete_table('votes_sessiondocument')

        # Removing M2M table for field sessions on 'SessionDocument'
        db.delete_table('votes_sessiondocument_sessions')

        # Deleting model 'Vote'
        db.delete_table('votes_vote')

        # Deleting model 'Keyword'
        db.delete_table('votes_keyword')

        # Deleting model 'SessionKeyword'
        db.delete_table('votes_sessionkeyword')
    
    
    models = {
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
            'name': ('django.db.models.fields.CharField', [], {'max_length': '10', 'primary_key': 'True'})
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
            'url_name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '20', 'db_index': 'True'})
        },
        'votes.session': {
            'Meta': {'object_name': 'Session'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info': ('django.db.models.fields.TextField', [], {}),
            'info_link': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'number': ('django.db.models.fields.IntegerField', [], {}),
            'plenary_session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['votes.PlenarySession']"}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'time': ('django.db.models.fields.TimeField', [], {}),
            'vote_counts': ('django.db.models.fields.CommaSeparatedIntegerField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'})
        },
        'votes.sessiondocument': {
            'Meta': {'object_name': 'SessionDocument'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info_link': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20', 'db_index': 'True'}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['votes.Session']", 'symmetrical': 'False'}),
            'url_name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '20', 'db_index': 'True'})
        },
        'votes.sessionkeyword': {
            'Meta': {'object_name': 'SessionKeyword'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keyword': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['votes.Keyword']"}),
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
            'name': ('django.db.models.fields.CharField', [], {'max_length': '40'})
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
