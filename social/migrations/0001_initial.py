# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Feed'
        db.create_table('social_feed', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('origin_id', self.gf('django.db.models.fields.CharField')(max_length=50, db_index=True)),
            ('interest', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('picture', self.gf('django.db.models.fields.URLField')(max_length=250, null=True)),
            ('account_name', self.gf('django.db.models.fields.CharField')(max_length=50, null=True)),
            ('last_update', self.gf('django.db.models.fields.DateTimeField')(null=True, db_index=True)),
            ('update_error_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal('social', ['Feed'])

        # Adding unique constraint on 'Feed', fields ['type', 'origin_id']
        db.create_unique('social_feed', ['type', 'origin_id'])

        # Adding model 'BrokenFeed'
        db.create_table('social_brokenfeed', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('origin_id', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
            ('account_name', self.gf('django.db.models.fields.CharField')(max_length=100, null=True)),
            ('check_time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('reason', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('social', ['BrokenFeed'])

        # Adding unique constraint on 'BrokenFeed', fields ['type', 'origin_id']
        db.create_unique('social_brokenfeed', ['type', 'origin_id'])

        # Adding model 'Update'
        db.create_table('social_update', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('feed', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['social.Feed'])),
            ('text', self.gf('django.db.models.fields.CharField')(max_length=4000, null=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('sub_type', self.gf('django.db.models.fields.CharField')(max_length=30, null=True)),
            ('created_time', self.gf('django.db.models.fields.DateTimeField')(db_index=True)),
            ('origin_id', self.gf('django.db.models.fields.CharField')(max_length=50, db_index=True)),
            ('interest', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('picture', self.gf('django.db.models.fields.URLField')(max_length=350, null=True)),
            ('share_link', self.gf('django.db.models.fields.URLField')(max_length=350, null=True)),
            ('share_title', self.gf('django.db.models.fields.CharField')(max_length=250, null=True)),
            ('share_caption', self.gf('django.db.models.fields.CharField')(max_length=600, null=True)),
            ('share_description', self.gf('django.db.models.fields.CharField')(max_length=600, null=True)),
        ))
        db.send_create_signal('social', ['Update'])

        # Adding unique constraint on 'Update', fields ['feed', 'origin_id']
        db.create_unique('social_update', ['feed_id', 'origin_id'])

        # Adding model 'ApiToken'
        db.create_table('social_apitoken', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('token', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('updated_time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('social', ['ApiToken'])


    def backwards(self, orm):
        # Removing unique constraint on 'Update', fields ['feed', 'origin_id']
        db.delete_unique('social_update', ['feed_id', 'origin_id'])

        # Removing unique constraint on 'BrokenFeed', fields ['type', 'origin_id']
        db.delete_unique('social_brokenfeed', ['type', 'origin_id'])

        # Removing unique constraint on 'Feed', fields ['type', 'origin_id']
        db.delete_unique('social_feed', ['type', 'origin_id'])

        # Deleting model 'Feed'
        db.delete_table('social_feed')

        # Deleting model 'BrokenFeed'
        db.delete_table('social_brokenfeed')

        # Deleting model 'Update'
        db.delete_table('social_update')

        # Deleting model 'ApiToken'
        db.delete_table('social_apitoken')


    models = {
        'social.apitoken': {
            'Meta': {'object_name': 'ApiToken'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'token': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'updated_time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'social.brokenfeed': {
            'Meta': {'unique_together': "(('type', 'origin_id'),)", 'object_name': 'BrokenFeed'},
            'account_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'check_time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'origin_id': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'reason': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '2'})
        },
        'social.feed': {
            'Meta': {'unique_together': "(('type', 'origin_id'),)", 'object_name': 'Feed'},
            'account_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interest': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'last_update': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'origin_id': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'picture': ('django.db.models.fields.URLField', [], {'max_length': '250', 'null': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'update_error_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        'social.update': {
            'Meta': {'ordering': "['-created_time']", 'unique_together': "(('feed', 'origin_id'),)", 'object_name': 'Update'},
            'created_time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'feed': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['social.Feed']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interest': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'origin_id': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'picture': ('django.db.models.fields.URLField', [], {'max_length': '350', 'null': 'True'}),
            'share_caption': ('django.db.models.fields.CharField', [], {'max_length': '600', 'null': 'True'}),
            'share_description': ('django.db.models.fields.CharField', [], {'max_length': '600', 'null': 'True'}),
            'share_link': ('django.db.models.fields.URLField', [], {'max_length': '350', 'null': 'True'}),
            'share_title': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
            'sub_type': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True'}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '4000', 'null': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        }
    }

    complete_apps = ['social']