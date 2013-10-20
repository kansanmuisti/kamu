class @Party extends Backbone.Tastypie.Model
    url: -> API_PREFIX + "party/#{@get('name')}/"
    get_logo_thumbnail: (width, height) ->
        return @url() + "logo/?dim=#{width}x#{height}"

class @PartyList extends Backbone.Tastypie.Collection
    url: API_PREFIX + 'party/'
    model: Party

class @Member extends Backbone.Tastypie.Model
    URL_PREFIX: '/member/'
    url: -> API_PREFIX + "member/#{@get('id')}/"
    get_view_url: -> "#{@URL_PREFIX}#{@get('url_name')}/"

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
    url: API_PREFIX + 'member/'
    model: Member

class @MemberActivity extends Backbone.Tastypie.Model

class @MemberActivityList extends Backbone.Tastypie.Collection
    url: API_PREFIX + 'member_activity/'
    model: MemberActivity
