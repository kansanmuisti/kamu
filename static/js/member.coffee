class @MemberActivityScoresView extends @ActivityScoresView
    initialize: (member, options) ->
        super (new MemberActivityScoresList member.get 'id'), options

class @MemberActivityFeedView extends Backbone.View
    el: ".activity-feed"
    initialize: (@member) ->
        @collection = new MemberActivityList()
        @collection.bind 'add', @add_item
        @collection.bind 'reset', @add_all_items
        @base_filters =
            member: @member.get 'id'
            limit: 20
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
            @user_filters['type__type__in'] = type.join(",")
        else
            delete @user_filters['type__type__in']
        @filter()

    add_item: (item) =>
        view = new ActivityView model: item, has_actor: false
        view.render()
        @$el.append view.el

    add_all_items: (coll) =>
        @$el.empty()
        coll.each @add_item

party_list = new PartyList party_json

tags = ({name: x[0], count: x[1], url: '#'} for x in keyword_activity)
tags = _.sortBy tags, (x) -> x.name
if tags.length > 0
    $("#member-tag-cloud").tag_cloud tags
else
    $("#member-tag-cloud").append("<h4>Ei asiasanoitettua aktiivisuutta</h4>")

feed_view = new MemberActivityFeedView member

$("#member-tag-cloud li a").click (ev) ->
    ev.preventDefault()
    if $(this).hasClass 'active'
        feed_view.filter_keyword()
        member_activity_scores_view.filter_keyword()
        $(this).removeClass 'active'
    else
        kw = $.trim $(@).html()
        feed_view.filter_keyword kw
        member_activity_scores_view.filter_keyword kw
        $("#member-tag-cloud li a").removeClass 'active'
        $(this).addClass 'active'

disable_filters = ->
    $(".feed-filter-buttons .filter-button").removeClass 'active'
    $(".feed-filter-buttons .disable-filters").addClass 'active'
    feed_view.filter_type null
    if typeof member_activity_scores_view != 'undefined'
        member_activity_scores_view.filter_type null

$(".feed-filter-buttons .disable-filters").click disable_filters
disable_filters()

$(".feed-filter-buttons .filter-button").click (ev) ->
    $btn = $(ev.currentTarget)
    type = $btn.data 'feed-type'
    $btn.toggleClass 'active'
    
    all_buttons = $(".feed-filter-buttons .filter-button")
    active_buttons = $(".feed-filter-buttons .filter-button.active")
    filters = ($(button).data("feed-type") for button in active_buttons)
    
    if filters.length == 0 or all_buttons.length == active_buttons.length
        disable_filters()
        return

    $(".feed-filter-buttons .disable-filters").removeClass 'active'
    feed_view.filter_type filters

    member_activity_scores_view.filter_type filters
