class @ActivityFeedView extends Backbone.View
    initialize: ({@collection, @el}) ->
        @collection.bind 'add', @add_item
        @collection.bind 'reset', @add_all_items
        @base_filters =
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
        view = new ActivityView model: item, has_actor: true
        view.render()
        @$el.append view.el

    add_all_items: (coll) =>
        @$el.empty()
        coll.each @add_item

class @ActivityFeedControl
    constructor: (@state) ->
        @type_state = @state.sub "type"
        @kw_state = @state.sub "keyword"

    feed_view: (view) => @state.on (opts={}) =>
        view.filter opts

    scores_view: (view) => @state.on (opts={}) =>
        view.filter_keyword @kw_state.get()
        types = @type_state.get()
        if types?
            types = (type for type of types)
        view.filter_type types

    tagcloud: (el) =>
        tagcloud_buttons = el.find("li a")
        kw_state = @kw_state
        tagcloud_buttons.click (ev) ->
            ev.preventDefault()
            btn = $(@)
            if btn.hasClass 'active'
                kw_state.update undefined
            else
                kw_state.update btn.data "id"
        @kw_state.on (value) ->
            tagcloud_buttons.removeClass "active"
            if not value?
                return
            tagcloud_buttons.filter("[data-id='#{value.toLowerCase()}']").addClass "active"
 
    controls: (el) =>
        kw_state = @kw_state
        type_state = @type_state
        
        kw_state.on (value) ->
            el.find(".tag-filter-input").val(value ? "")
        el.find(".tag-filter-input").change -> kw_state.update $(@).val()
        
        filter_buttons = $(".feed-filter-buttons")
        
        filter_buttons.find(".disable-filters").click ->
            type_state.update undefined
        
        group_is_active = (grp, state) ->
            for btn in grp.find ".filter-button"
                    return true if type_state.sub($(btn).data("feed-type")).get()
            return false

        type_state.on (types) ->
            filter_buttons.find(".disable-filters").toggleClass "active", not types?
            groups = filter_buttons.find(".feed-type-group")
            for grp in groups
                btn = $(grp).find("> .filter-group-button")
                btn.toggleClass "active", group_is_active $(grp)
                    
        
        filter_buttons.find(".filter-button").each ->
            btn = $(@)
            state = type_state.sub(btn.data("feed-type"))
            btn.click -> state.update if btn.hasClass("active") then undefined else 1
            state.on (value) -> btn.toggleClass "active", Boolean(value)
        
        $(".filter-group-button").click ->
            update = {}
            grp = $(@)
            value = if grp.hasClass("active") then undefined else 1
            for btn in grp.parent().find(".filter-button")
                update[$(btn).data('feed-type')] = value
            type_state.update update

