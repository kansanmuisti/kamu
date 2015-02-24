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

    filter: ({keyword, type}={}) ->
        params = {}
        if keyword?
            params.keyword = keyword
        if type?
            params.type__type__in = (t for t of type).join(",")
        
        _.extend params, @base_filters
        @collection.fetch
            reset: true
            data: params
    
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

mpact_state = hashstate.sub "mpact"
type_state = mpact_state.sub "type"
mpact_state.on (opts) ->
    feed_view.filter opts
    #member_activity_scores_view.filter opts

$("#member-tag-cloud li a").click (ev) ->
    ev.preventDefault()
    # TODO: Don't use the class as state!
    if $(this).hasClass 'active'
        mpact_state.update keyword: undefined
        $(this).removeClass 'active'
    else
        kw = $.trim $(@).html()
        mpact_state.update keyword: kw
        $("#member-tag-cloud li a").removeClass 'active'
        $(this).addClass 'active'

disable_filters = ->
    $(".feed-filter-buttons .filter-button").removeClass 'active'
    $(".feed-filter-buttons .disable-filters").addClass 'active'
    mpact_state.update type: undefined

$(".feed-filter-buttons .disable-filters").click disable_filters

$(".feed-filter-buttons .filter-button").each ->
    btn = $(@)
    state = type_state.sub(btn.data("feed-type"))
    btn.click -> state.update if btn.hasClass("active") then undefined else 1
    state.on (value) -> btn.toggleClass "active", Boolean(value)

