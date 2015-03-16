from haystack import indexes
from parliament.models import Member, Keyword, MemberActivity, Term


class MemberIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, model_attr='name', use_template=False)
    autosuggest = indexes.EdgeNgramField(model_attr='name')
    time = indexes.DateTimeField(null=True)

    def get_updated_field(self):
        return 'last_modified_time'

    def get_model(self):
        return Member

    def index_queryset(self, using=None):
        term = Term.objects.latest()
        return self.get_model().objects.active_in_term(term)

    def prepare(self, obj):
        data = super(MemberIndex, self).prepare(obj)
        data['boost'] = 2.0
        return data


class KeywordIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, model_attr='name', use_template=False)
    autosuggest = indexes.EdgeNgramField(model_attr='name')
    time = indexes.DateTimeField(null=True)

    def get_updated_field(self):
        return 'last_modified_time'

    def get_model(self):
        return Keyword

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare(self, obj):
        data = super(KeywordIndex, self).prepare(obj)
        data['boost'] = 1.5
        return data


class MemberActivityIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True)
    time = indexes.DateTimeField(model_attr='time')
    type = indexes.CharField(model_attr='type__type', faceted=True)
    member = indexes.CharField(model_attr='member__name', faceted=True, null=True)
    autosuggest = indexes.EdgeNgramField(null=True)

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

    def prepare_autosuggest(self, obj):
        target = obj.get_target_info()
        if 'subject' in target:
            return target['subject']
        else:
            return None

    def get_model(self):
        return MemberActivity

    def index_queryset(self, using=None):
        # Exclude signature events from indexing.
        queryset = MemberActivity.objects.exclude(type='SI')
        return queryset

    def build_queryset(self, using=None, start_date=None, end_date=None):
        queryset = super(MemberActivityIndex, self).build_queryset(using, start_date, end_date)
        # FIXME
        return queryset[:1000]
