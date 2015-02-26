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

$ ->
	party_list = new PartyList party_json
	
	tags = ({name: x[0], id: x[0].toLowerCase(), count: x[1]} for x in keyword_activity)
	tags = _.sortBy tags, (x) -> x.name
	if tags.length > 0
	    $("#member-tag-cloud").tag_cloud tags
	else
	    $("#member-tag-cloud").append("<h4>Ei asiasanoitettua aktiivisuutta</h4>")
	
	feed_view = new MemberActivityFeedView member
	
	mpact_state = hashstate.sub "as"
	type_state = mpact_state.sub "type"
	kw_state = mpact_state.sub "keyword"
	mpact_state.on (opts={}) ->
        feed_view.filter opts
        
        member_activity_scores_view.filter_keyword opts.keyword
        types = opts.type
        if types?
            types = (type for type of types)
        member_activity_scores_view.filter_type types
	
	tagcloud_buttons = $("#member-tag-cloud li a")
	tagcloud_buttons.click (ev) ->
	    ev.preventDefault()
	    btn = $(@)
	    if btn.hasClass 'active'
	        kw_state.update undefined
	    else
	        kw_state.update btn.data "id"
	
	kw_state.on (value) ->
        $(".feed-filters .tag-filter-input").val(value ? "")
        tagcloud_buttons.removeClass "active"
        if not value?
            return
        tagcloud_buttons.filter("[data-id='#{value.toLowerCase()}']").addClass "active"
	
	filter_buttons = $(".feed-filter-buttons .filter-button")
	
	$(".feed-filter-buttons .disable-filters").click ->
	    type_state.update undefined
	
	type_state.on (types) ->
	    $(".feed-filter-buttons .disable-filters").toggleClass "active", not types?
	
	filter_buttons.each ->
	    btn = $(@)
	    state = type_state.sub(btn.data("feed-type"))
	    btn.click -> state.update if btn.hasClass("active") then undefined else 1
	    state.on (value) -> btn.toggleClass "active", Boolean(value)

    $(".feed-filters .tag-filter-input").change -> kw_state.update $(@).val()
        
	
