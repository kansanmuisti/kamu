# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'QuestionSource'
        db.create_table('opinions_questionsource', (
            ('year', self.gf('django.db.models.fields.IntegerField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('opinions', ['QuestionSource'])

        # Adding unique constraint on 'QuestionSource', fields ['name', 'year']
        db.create_unique('opinions_questionsource', ['name', 'year'])

        # Adding model 'Question'
        db.create_table('opinions_question', (
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('weight', self.gf('django.db.models.fields.IntegerField')(unique=True)),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['opinions.QuestionSource'])),
        ))
        db.send_create_signal('opinions', ['Question'])

        # Adding unique constraint on 'Question', fields ['weight', 'source']
        db.create_unique('opinions_question', ['weight', 'source_id'])

        # Adding model 'Option'
        db.create_table('opinions_option', (
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['opinions.Question'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('weight', self.gf('django.db.models.fields.IntegerField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('opinions', ['Option'])

        # Adding unique constraint on 'Option', fields ['question', 'weight']
        db.create_unique('opinions_option', ['question_id', 'weight'])

        # Adding model 'Answer'
        db.create_table('opinions_answer', (
            ('member', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['votes.Member'])),
            ('explanation', self.gf('django.db.models.fields.TextField')()),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['opinions.Question'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('option', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['opinions.Option'], null=True)),
        ))
        db.send_create_signal('opinions', ['Answer'])

        # Adding unique constraint on 'Answer', fields ['member', 'option']
        db.create_unique('opinions_answer', ['member_id', 'option_id'])

        # Adding model 'VoteOptionCongruence'
        db.create_table('opinions_voteoptioncongruence', (
            ('option', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['opinions.Option'])),
            ('congruence', self.gf('django.db.models.fields.FloatField')()),
            ('session', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['votes.Session'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('vote', self.gf('django.db.models.fields.CharField')(max_length=1, db_index=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('opinions', ['VoteOptionCongruence'])

        # Adding unique constraint on 'VoteOptionCongruence', fields ['user', 'option', 'session', 'vote']
        db.create_unique('opinions_voteoptioncongruence', ['user_id', 'option_id', 'session_id', 'vote'])

        # Adding model 'QuestionSessionRelevance'
        db.create_table('opinions_questionsessionrelevance', (
            ('relevance', self.gf('django.db.models.fields.FloatField')()),
            ('session', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['votes.Session'])),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['opinions.Question'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
        ))
        db.send_create_signal('opinions', ['QuestionSessionRelevance'])

        # Adding unique constraint on 'QuestionSessionRelevance', fields ['question', 'session', 'user']
        db.create_unique('opinions_questionsessionrelevance', ['question_id', 'session_id', 'user_id'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'QuestionSource'
        db.delete_table('opinions_questionsource')

        # Removing unique constraint on 'QuestionSource', fields ['name', 'year']
        db.delete_unique('opinions_questionsource', ['name', 'year'])

        # Deleting model 'Question'
        db.delete_table('opinions_question')

        # Removing unique constraint on 'Question', fields ['weight', 'source']
        db.delete_unique('opinions_question', ['weight', 'source_id'])

        # Deleting model 'Option'
        db.delete_table('opinions_option')

        # Removing unique constraint on 'Option', fields ['question', 'weight']
        db.delete_unique('opinions_option', ['question_id', 'weight'])

        # Deleting model 'Answer'
        db.delete_table('opinions_answer')

        # Removing unique constraint on 'Answer', fields ['member', 'option']
        db.delete_unique('opinions_answer', ['member_id', 'option_id'])

        # Deleting model 'VoteOptionCongruence'
        db.delete_table('opinions_voteoptioncongruence')

        # Removing unique constraint on 'VoteOptionCongruence', fields ['user', 'option', 'session', 'vote']
        db.delete_unique('opinions_voteoptioncongruence', ['user_id', 'option_id', 'session_id', 'vote'])

        # Deleting model 'QuestionSessionRelevance'
        db.delete_table('opinions_questionsessionrelevance')

        # Removing unique constraint on 'QuestionSessionRelevance', fields ['question', 'session', 'user']
        db.delete_unique('opinions_questionsessionrelevance', ['question_id', 'session_id', 'user_id'])
    
    
    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'opinions.answer': {
            'Meta': {'unique_together': "(('member', 'option'),)", 'object_name': 'Answer'},
            'explanation': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['votes.Member']"}),
            'option': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['opinions.Option']", 'null': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['opinions.Question']"})
        },
        'opinions.option': {
            'Meta': {'unique_together': "(('question', 'weight'),)", 'object_name': 'Option'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['opinions.Question']"}),
            'weight': ('django.db.models.fields.IntegerField', [], {})
        },
        'opinions.question': {
            'Meta': {'unique_together': "(('weight', 'source'),)", 'object_name': 'Question'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['opinions.QuestionSource']"}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'weight': ('django.db.models.fields.IntegerField', [], {'unique': 'True'})
        },
        'opinions.questionsessionrelevance': {
            'Meta': {'unique_together': "(('question', 'session', 'user'),)", 'object_name': 'QuestionSessionRelevance'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['opinions.Question']"}),
            'relevance': ('django.db.models.fields.FloatField', [], {}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['votes.Session']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        'opinions.questionsource': {
            'Meta': {'unique_together': "(('name', 'year'),)", 'object_name': 'QuestionSource'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'year': ('django.db.models.fields.IntegerField', [], {})
        },
        'opinions.voteoptioncongruence': {
            'Meta': {'unique_together': "(('user', 'option', 'session', 'vote'),)", 'object_name': 'VoteOptionCongruence'},
            'congruence': ('django.db.models.fields.FloatField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'option': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['opinions.Option']"}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['votes.Session']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'vote': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'})
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
        'votes.party': {
            'Meta': {'object_name': 'Party'},
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'info_link': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'logo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '10', 'primary_key': 'True'})
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
        }
    }
    
    complete_apps = ['opinions']
