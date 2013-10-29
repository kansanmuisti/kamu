class @Party extends Backbone.Tastypie.Model
    URL_PREFIX: '/party/'
    url: ->
        URL_CONFIG['api_party'] + @get('name') + '/'
    get_logo_thumbnail: (width, height) ->
        return @url() + "logo/?dim=#{width}x#{height}"
    get_view_url: ->
        URL_CONFIG['party_details'].replace 'PARTY', @get('name')

class @PartyList extends Backbone.Tastypie.Collection
    urlRoot: URL_CONFIG['api_party']
    model: Party

# models for templates/member

class @Member extends Backbone.Tastypie.Model
    url: ->
        URL_CONFIG['api_member'] + @get('id')
    get_view_url: ->
        URL_CONFIG['member_details'].replace 'MEMBER', @get('url_name')

    initialize: (models, opts) ->
        # Augment the stats object with some items
        if not @attributes.stats
            @attributes.stats = {}
        @attributes.stats.term_count = @attributes.terms.length

    toJSON: (options) ->
        ret = super options
        ret.is_minister = @is_minister()
        ret.view_url = @get_view_url()
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



class @MemberActivity extends Backbone.Tastypie.Model

class @MemberActivityList extends Backbone.Tastypie.Collection
    urlRoot: URL_CONFIG['api_member_activity']
    model: MemberActivity

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
