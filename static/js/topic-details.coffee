class @TopicActivityScoresView extends @ActivityScoresView
    initialize: (topic, options) ->
        super (new KeywordActivityScoresList topic.get 'id'), options

class FeedFilterButtonsView extends Backbone.View
    el: '.feed-filters .btn-toolbar'
    events:
        'click .filter-button': 'handle_button_click'
        'click .disable-filters': 'disable_filters'
    initialize: (options) ->
        @filter_groups = options.filter_groups
        @feed_view = options.feed_view
        @disable_button_opts = options.disable_button_opts

    handle_button_click: (ev) ->
        btn_el = $(ev.currentTarget)
        btn_el.toggleClass 'active'

        types = []
        for btn in @buttons
            if btn.hasClass 'active'
                types.push btn.data 'filter-type'
        if types.length == 0
            @disable_filters()
            return

        @disable_button.removeClass 'active'
        @feed_view.set_filter types
    
    disable_filters: ->
        @feed_view.set_filter null
        for btn in @buttons
            btn.removeClass 'active'
        @disable_button.addClass 'active'

    render: ->
        @$el.empty()
        @buttons = []
        
        new_button = (f) ->
            el = $("<button class='btn btn-small btn-default filter-button' type='button' />")
            if f.icon
                el.append $("<i class='typcn typcn-#{f.icon}' />")
                el.attr 'title', f.name
            else
                el.html f.name
            el.data 'filter-type', f.type
            if f.button_type
                el.addClass('btn-' + f.button_type)
            
            return el

        for group in @filter_groups
            grp_el = $('<div class="btn-group" />')
            for f in group.filters
                el = new_button f
                grp_el.append el
                @buttons.push el
            @$el.append grp_el
        @disable_button = new_button @disable_button_opts
        @disable_button.removeClass('filter-button')
        @disable_button.addClass('disable-filters')

        disable_group = $('<div class="btn-group" />')
        disable_group.append @disable_button
        @$el.append disable_group
        @disable_filters()

class TopicFeedView extends Backbone.View
    el: 'ul.activity-feed'
    initialize: (opts) ->
        @keyword = opts.keyword
        @supported_types = opts.supported_types
        @collection = new KeywordActivityList
        @collection.filters['keyword'] = @keyword.get 'id'
        @listenTo @collection, 'reset', @render_all
        @set_filter null

    render_one: (model) ->
        activity = new MemberActivity(model.get 'activity')
        view = new ActivityView model: activity, has_actor: true
        view.render()
        @$el.append view.$el

    render_all: ->
        @$el.empty()
        @collection.each (model) =>
            @render_one model

    set_filter: (types) ->
        fname = 'activity__type__in'
        if not types
            delete @collection.filters[fname]
        else
            @collection.filters[fname] = types.join(',')
        @collection.fetch reset: true

SUPPORTED_TYPES = ['IN', 'GB', 'WQ']

keyword = new Keyword keyword_json
feed_view = new TopicFeedView keyword: keyword, supported_types: SUPPORTED_TYPES

parliament_filters = (f for f in FEED_FILTERS.parliament when f.type in SUPPORTED_TYPES)
feed_filters = [
    {name: "parliament", filters: parliament_filters},
]

feed_filter_buttons = new FeedFilterButtonsView
    filter_groups: feed_filters
    feed_view: feed_view
    disable_button_opts: FEED_FILTER_ALL

feed_filter_buttons.render()

#
# Related keywords
#
related_tags = []
for kw_dict in keyword.get('related')[0..10]
    kw = new Keyword kw_dict
    tag =
        name: kw.get 'name'
        id: kw.get 'id'
        count: kw.get 'count'
        url: kw.get_view_url()
    related_tags.push tag

related_tags = _.sortBy related_tags, (t) -> t.name
$(".feature-tagcloud .tagcloud").tag_cloud related_tags

#
# Most active MPs and parties
#
most_active = keyword.get 'most_active'
$ul = $(".most-active-parties ul")
template = _.template $.trim $("#most-active-party-template").html()
for p in most_active.parties[0..4]
    party = new Party p
    dict = party.toJSON()
    dict.thumbnail_url = party.get_logo_thumbnail(64, 64)
    $ul.append $(template(dict))

$ul = $(".most-active-members ul")
template = _.template $.trim $("#most-active-member-template").html()
for mp in most_active.members[0..9]
    member = new Member mp
    dict = member.toJSON()
    dict.thumbnail_url = member.get_portrait_thumbnail(64)
    $ul.append $(template(dict))
