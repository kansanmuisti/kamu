"""from djapian import space, Indexer, CompositeIndexer

from kamu.votes.models import *

class MemberIndexer(Indexer):
    fields = ['name', 'given_names', 'surname', 'email', 'phone']
space.add_index(Member, MemberIndexer, attach_as='indexer')

class SessionIndexer(Indexer):
    fields = ['info', 'subject']
space.add_index(Session, SessionIndexer, attach_as='indexer')

class StatementIndexer(Indexer):
    fields = ['text']
space.add_index(Statement, StatementIndexer, attach_as='indexer')

complete_indexer = CompositeIndexer(Member.indexer, Session.indexer, Statement.indexer)
"""
