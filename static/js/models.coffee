class @Party extends Backbone.Tastypie.Model
    url: ->
        URL_CONFIG['api_party'] + @get('name') + '/'
    get_logo_thumbnail: (width, height) ->
        return @url() + "logo/?dim=#{width}x#{height}"
    get_view_url: ->
        URL_CONFIG['party_details'].replace 'PARTY', @get('name')

    toJSON: (options) ->
        ret = super options
        ret.view_url = @get_view_url()
        return ret

class @PartyList extends Backbone.Tastypie.Collection
    urlRoot: URL_CONFIG['api_party']
    model: Party

# models for templates/member

class @Member extends Backbone.Tastypie.Model
    url: ->
        URL_CONFIG['api_member'] + @get('id') + '/'
    get_view_url: ->
        URL_CONFIG['member_details'].replace 'MEMBER', @get('url_name')

    get_portrait_thumbnail: (width) ->
        height = 3 * width / 2
        return @url() + "portrait/?dim=#{width}x#{height}"

    initialize: (models, opts) ->
        # Augment the stats object with some items
        if not @attributes.stats
            @attributes.stats = {}
        if @attributes.terms
            @attributes.stats.term_count = @attributes.terms.length

    toJSON: (options) ->
        ret = super options
        ret.view_url = @get_view_url()
        posts = @get('posts')
        if posts
            ret.is_minister = @is_minister()
            ministry_posts = @get('posts').ministry
            if ministry_posts.length
                label = ministry_posts[0].label
                label = label.charAt(0).toUpperCase() + label.slice(1)
                ret.minister = label
            else
                ret.minister = null

        return ret

    is_minister: ->
        return @get('posts').ministry.length > 0

    get_party: (party_list) ->
        return party_list.get @get('party')

class @MemberList extends Backbone.Tastypie.Collection
    urlRoot: URL_CONFIG['api_member']
    model: Member

class @ActivityScores extends Backbone.Tastypie.Model

class @ParliamentActivityScoresList extends Backbone.Tastypie.Collection
    initialize: ->
        @urlRoot = URL_CONFIG['api_parliament_activity_scores']
    model: ActivityScores

class @MemberActivityScoresList extends Backbone.Tastypie.Collection
    initialize: (member_id) ->
        @urlRoot = URL_CONFIG['api_member_activity_scores'].replace('999', member_id)
    model: ActivityScores

class @KeywordActivityScoresList extends Backbone.Tastypie.Collection
    initialize: (keyword_id) ->
        @urlRoot = URL_CONFIG['api_keyword_activity_scores'].replace('999', keyword_id)
    model: ActivityScores

class @MemberActivity extends Backbone.Tastypie.Model

class @MemberActivityList extends Backbone.Tastypie.Collection
    urlRoot: URL_CONFIG['api_member_activity']
    model: MemberActivity

class @Document extends Backbone.Tastypie.Model

class DocumentList extends Backbone.Tastypie.Collection
    urlRoot: URL_CONFIG['api_document']
    model: Document

class @Keyword extends Backbone.Tastypie.Model
    get_view_url: ->
        URL_CONFIG['topic_details'].replace('999', @get('id')).replace('SLUG', @get('slug'))

class @KeywordList extends Backbone.Tastypie.Collection
    urlRoot: URL_CONFIG['api_keyword']
    model: Keyword

class @KeywordActivity extends Backbone.Tastypie.Model

class @KeywordActivityList extends Backbone.Tastypie.Collection
    urlRoot: URL_CONFIG['api_keyword_activity']
    model: KeywordActivity
