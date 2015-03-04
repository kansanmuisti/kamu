from haystack import indexes
from parliament.models import Member, Statement, Document, MemberActivity
from social.models import Update


class MemberIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, model_attr='name', use_template=False)
    autosuggest = indexes.EdgeNgramField(model_attr='name')

    def get_updated_field(self):
        return 'last_modified_time'

    def get_model(self):
        return Member

    def index_queryset(self, using=None):
        return self.get_model().objects.current()

    def prepare(self, obj):
        data = super(MemberIndex, self).prepare(obj)
        data['boost'] = 2.0
        return data


class MemberActivityIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True)
    time = indexes.DateTimeField(model_attr='time')
    type = indexes.CharField(model_attr='type__type', faceted=True)
    member = indexes.CharField(model_attr='member__name', faceted=True)

    def get_updated_field(self):
        return 'last_modified_time'

    def prepare_text(self, obj):
        target = obj.get_target_info()
        text = []
        if 'name' in target:
            text.append(target['name'])
        if 'subject' in target:
            text.append(target['subject'])
        if 'text' in target:
            text.append(target['text'])
        return '\n'.join(text)

    def get_model(self):
        return MemberActivity

    def index_queryset(self, using=None):
        # Exclude signature events from indexing.
        queryset = MemberActivity.objects.exclude(type='SI')
        return queryset
