class @PartyActivityFeedView extends Backbone.View
    ### 
    Shows the activity feed for a party, very similar to the one
    for a member, just filter for party instead of member.
    ###
    el: ".activity-feed"
    initialize: (options) ->
        @collection = new MemberActivityList()
        @collection.bind 'add', @add_item
        @collection.bind 'reset', @add_all_items
        @base_filters =
            limit: 20
            member__party: options.party_id
        @user_filters = {}
        @filter()

    filter: ->
        params = _.clone @base_filters
        _.extend params, @user_filters
        @collection.fetch
            reset: true
            data: params

    filter_keyword: (kw) ->
        if kw
            @user_filters['keyword'] = kw
        else
            delete @user_filters['keyword']
        @filter()

    filter_type: (type) ->
        if type
            @user_filters['type__type'] = type
        else
            delete @user_filters['type__type']
        @filter()

    add_item: (item) =>
        view = new ActivityView model: item, has_actor: true
        view.render()
        @$el.append view.el

    add_all_items: (coll) =>
        @$el.empty()
        coll.each @add_item

tags = ({name: x[0], count: x[1], url: '#'} for x in keyword_activity)
tags = _.sortBy tags, (x) -> x.name
$("#party-tag-cloud").tag_cloud tags

feed_view = new PartyActivityFeedView party_id: party_json['id']

$("#party-tag-cloud li a").click (ev) ->
    ev.preventDefault()
    if $(this).hasClass 'active'
        feed_view.filter_keyword()
        $(this).removeClass 'active'
    else
        kw = $.trim $(@).html()
        feed_view.filter_keyword kw
        $("#member-tag-cloud li a").removeClass 'active'
        $(this).addClass 'active'

$(".feed-filter-buttons button").click (ev) ->
    $btn = $(ev.currentTarget)
    type = $btn.data 'feed-type'
    if $btn.hasClass 'active'
        $btn.removeClass 'active'
        feed_view.filter_type()
    else
        $(".feed-filter-buttons button").removeClass 'active'
        $btn.addClass 'active'
        feed_view.filter_type type
