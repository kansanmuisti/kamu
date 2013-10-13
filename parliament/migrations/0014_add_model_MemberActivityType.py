# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'MemberActivityType'
        db.create_table(u'parliament_memberactivitytype', (
            ('type', self.gf('django.db.models.fields.CharField')(max_length=5, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('weight', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal('parliament', ['MemberActivityType'])


    def backwards(self, orm):
        # Deleting model 'MemberActivityType'
        db.delete_table(u'parliament_memberactivitytype')


    models = {
        'parliament.committee': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Committee'},
            'current': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'origin_id': ('django.db.models.fields.CharField', [], {'max_length': '20', 'unique': 'True', 'null': 'True'}),
            'url_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'unique': 'True', 'null': 'True'})
        },
        'parliament.committeeassociation': {
            'Meta': {'object_name': 'CommitteeAssociation'},
            'begin': ('django.db.models.fields.DateField', [], {}),
            'committee': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Committee']"}),
            'end': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Member']"}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True'})
        },
        'parliament.committeedissentactivity': {
            'Meta': {'ordering': "('time', 'member__name')", 'object_name': 'CommitteeDissentActivity', '_ormbases': ['parliament.MemberActivity']},
            'doc': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Document']"}),
            u'memberactivity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['parliament.MemberActivity']", 'unique': 'True', 'primary_key': 'True'})
        },
        'parliament.district': {
            'Meta': {'object_name': 'District'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'long_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'})
        },
        'parliament.districtassociation': {
            'Meta': {'unique_together': "(('member', 'begin'),)", 'object_name': 'DistrictAssociation'},
            'begin': ('django.db.models.fields.DateField', [], {}),
            'district': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.District']", 'null': 'True'}),
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Member']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'})
        },
        'parliament.document': {
            'Meta': {'ordering': "('date',)", 'unique_together': "(('type', 'name'),)", 'object_name': 'Document'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Member']", 'null': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'error': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info_link': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'keywords': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['parliament.Keyword']", 'symmetrical': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'}),
            'origin_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'}),
            'related_docs': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'related_docs_rel_+'", 'to': "orm['parliament.Document']"}),
            'sgml_link': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'subject': ('django.db.models.fields.TextField', [], {}),
            'summary': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'update_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'url_name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '20'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'})
        },
        'parliament.documentprocessingstage': {
            'Meta': {'unique_together': "(('doc', 'stage'), ('doc', 'index'))", 'object_name': 'DocumentProcessingStage'},
            'date': ('django.db.models.fields.DateField', [], {}),
            'doc': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Document']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'stage': ('django.db.models.fields.CharField', [], {'max_length': '15', 'db_index': 'True'})
        },
        'parliament.documentsignature': {
            'Meta': {'unique_together': "(('doc', 'member'),)", 'object_name': 'DocumentSignature'},
            'date': ('django.db.models.fields.DateField', [], {}),
            'doc': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Document']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Member']"})
        },
        'parliament.funding': {
            'Meta': {'unique_together': "(('member', 'term', 'type', 'source'),)", 'object_name': 'Funding'},
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Member']"}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.FundingSource']", 'null': 'True', 'blank': 'True'}),
            'term': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Term']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '6'})
        },
        'parliament.fundingsource': {
            'Meta': {'object_name': 'FundingSource'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'})
        },
        'parliament.governingparty': {
            'Meta': {'object_name': 'GoverningParty'},
            'begin': ('django.db.models.fields.DateField', [], {}),
            'end': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'government': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Government']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Party']"})
        },
        'parliament.government': {
            'Meta': {'object_name': 'Government'},
            'begin': ('django.db.models.fields.DateField', [], {}),
            'end': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'parliament.initiativeactivity': {
            'Meta': {'ordering': "('time', 'member__name')", 'object_name': 'InitiativeActivity', '_ormbases': ['parliament.MemberActivity']},
            'doc': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Document']"}),
            u'memberactivity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['parliament.MemberActivity']", 'unique': 'True', 'primary_key': 'True'})
        },
        'parliament.keyword': {
            'Meta': {'object_name': 'Keyword'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128', 'db_index': 'True'})
        },
        'parliament.keywordactivity': {
            'Meta': {'unique_together': "(('activity', 'keyword'),)", 'object_name': 'KeywordActivity'},
            'activity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.MemberActivity']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keyword': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Keyword']"})
        },
        'parliament.member': {
            'Meta': {'object_name': 'Member'},
            'birth_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'birth_place': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'given_names': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'homepage_link': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info_link': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'origin_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '20', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Party']", 'null': 'True', 'blank': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'photo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'summary': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'surname': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'url_name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'wikipedia_link': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        'parliament.memberactivity': {
            'Meta': {'ordering': "('time', 'member__name')", 'object_name': 'MemberActivity'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Member']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.MemberActivityType']"})
        },
        'parliament.memberactivitytype': {
            'Meta': {'object_name': 'MemberActivityType'},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '5', 'primary_key': 'True'}),
            'weight': ('django.db.models.fields.FloatField', [], {})
        },
        'parliament.memberseat': {
            'Meta': {'unique_together': "(('member', 'begin', 'end'), ('seat', 'begin', 'end'))", 'object_name': 'MemberSeat'},
            'begin': ('django.db.models.fields.DateField', [], {}),
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Member']"}),
            'seat': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Seat']"})
        },
        'parliament.membersocialfeed': {
            'Meta': {'object_name': 'MemberSocialFeed', '_ormbases': [u'social.Feed']},
            u'feed_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['social.Feed']", 'unique': 'True', 'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Member']"})
        },
        'parliament.memberstats': {
            'Meta': {'object_name': 'MemberStats'},
            'begin': ('django.db.models.fields.DateField', [], {}),
            'election_budget': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Member']"}),
            'party_agreement': ('django.db.models.fields.CommaSeparatedIntegerField', [], {'max_length': '20'}),
            'session_agreement': ('django.db.models.fields.CommaSeparatedIntegerField', [], {'max_length': '20'}),
            'statement_count': ('django.db.models.fields.IntegerField', [], {}),
            'vote_counts': ('django.db.models.fields.CommaSeparatedIntegerField', [], {'max_length': '30'})
        },
        'parliament.ministryassociation': {
            'Meta': {'object_name': 'MinistryAssociation'},
            'begin': ('django.db.models.fields.DateField', [], {}),
            'end': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Member']"}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'parliament.party': {
            'Meta': {'object_name': 'Party'},
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'homepage_link': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'logo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10', 'db_index': 'True'}),
            'vis_color': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'})
        },
        'parliament.partyassociation': {
            'Meta': {'object_name': 'PartyAssociation'},
            'begin': ('django.db.models.fields.DateField', [], {}),
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Member']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Party']", 'null': 'True'})
        },
        'parliament.plenarysession': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'PlenarySession'},
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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
            'docs': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['parliament.Document']", 'through': "orm['parliament.PlenarySessionItemDocument']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nr_statements': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'nr_votes': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'number': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'plsess': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.PlenarySession']"}),
            'sub_description': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'sub_number': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '15'})
        },
        'parliament.plenarysessionitemdocument': {
            'Meta': {'ordering': "('order',)", 'unique_together': "(('item', 'doc'),)", 'object_name': 'PlenarySessionItemDocument'},
            'doc': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Document']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.PlenarySessionItem']"}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'parliament.plenaryvote': {
            'Meta': {'ordering': "('plsess__date', 'number')", 'object_name': 'PlenaryVote'},
            'docs': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['parliament.Document']", 'through': "orm['parliament.PlenaryVoteDocument']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info_link': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'keywords': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['parliament.Keyword']", 'symmetrical': 'False'}),
            'number': ('django.db.models.fields.IntegerField', [], {}),
            'plsess': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.PlenarySession']"}),
            'plsess_item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.PlenarySessionItem']", 'null': 'True', 'blank': 'True'}),
            'setting': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'subject': ('django.db.models.fields.TextField', [], {}),
            'time': ('django.db.models.fields.DateTimeField', [], {}),
            'vote_counts': ('django.db.models.fields.CommaSeparatedIntegerField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'})
        },
        'parliament.plenaryvotedocument': {
            'Meta': {'object_name': 'PlenaryVoteDocument'},
            'doc': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Document']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.PlenaryVote']"})
        },
        'parliament.rebelvoteactivity': {
            'Meta': {'ordering': "('time', 'member__name')", 'object_name': 'RebelVoteActivity', '_ormbases': ['parliament.MemberActivity']},
            u'memberactivity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['parliament.MemberActivity']", 'unique': 'True', 'primary_key': 'True'}),
            'vote': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Vote']", 'unique': 'True'})
        },
        'parliament.seat': {
            'Meta': {'unique_together': "(('row', 'seat'),)", 'object_name': 'Seat'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'row': ('django.db.models.fields.IntegerField', [], {}),
            'seat': ('django.db.models.fields.IntegerField', [], {}),
            'x': ('django.db.models.fields.FloatField', [], {}),
            'y': ('django.db.models.fields.FloatField', [], {})
        },
        'parliament.signatureactivity': {
            'Meta': {'ordering': "('time', 'member__name')", 'object_name': 'SignatureActivity', '_ormbases': ['parliament.MemberActivity']},
            u'memberactivity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['parliament.MemberActivity']", 'unique': 'True', 'primary_key': 'True'}),
            'signature': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.DocumentSignature']", 'unique': 'True'})
        },
        'parliament.socialupdateactivity': {
            'Meta': {'ordering': "('time', 'member__name')", 'object_name': 'SocialUpdateActivity', '_ormbases': ['parliament.MemberActivity']},
            u'memberactivity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['parliament.MemberActivity']", 'unique': 'True', 'primary_key': 'True'}),
            'update': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['social.Update']", 'unique': 'True'})
        },
        'parliament.statement': {
            'Meta': {'ordering': "('item', 'index')", 'unique_together': "(('item', 'index'),)", 'object_name': 'Statement'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.PlenarySessionItem']"}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Member']", 'null': 'True'}),
            'speaker_name': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'speaker_role': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '15'})
        },
        'parliament.statementactivity': {
            'Meta': {'ordering': "('time', 'member__name')", 'object_name': 'StatementActivity', '_ormbases': ['parliament.MemberActivity']},
            u'memberactivity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['parliament.MemberActivity']", 'unique': 'True', 'primary_key': 'True'}),
            'statement': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Statement']", 'unique': 'True'})
        },
        'parliament.term': {
            'Meta': {'ordering': "('-begin',)", 'object_name': 'Term'},
            'begin': ('django.db.models.fields.DateField', [], {}),
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'parliament.termmember': {
            'Meta': {'object_name': 'TermMember'},
            'election_budget': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Member']"}),
            'term': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Term']"})
        },
        'parliament.vote': {
            'Meta': {'object_name': 'Vote'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.Member']"}),
            'party': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['parliament.PlenaryVote']"}),
            'vote': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'})
        },
        u'social.feed': {
            'Meta': {'unique_together': "(('type', 'origin_id'),)", 'object_name': 'Feed'},
            'account_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interest': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'last_update': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'origin_id': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'picture': ('django.db.models.fields.URLField', [], {'max_length': '250', 'null': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'update_error_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        u'social.update': {
            'Meta': {'ordering': "['-created_time']", 'unique_together': "(('feed', 'origin_id'),)", 'object_name': 'Update'},
            'created_time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'feed': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['social.Feed']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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

    complete_apps = ['parliament']