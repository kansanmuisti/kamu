class @ActivityFeedView extends Backbone.View
    initialize: ({@collection, @el, default_filters}) ->
        @collection.bind 'add', @add_item
        @collection.bind 'reset', @add_all_items
        @all_loaded = false
        
        @base_filters = {}
        _.extend @base_filters, default_filters
        
        @filters = {}

    filter: ({keyword, type, date}={}) ->
        @collection.filters.offset = 0
        @collection.filters.limit = 20
        params = {}
        if keyword?
            params.keyword = keyword
        if type?
            params.type__type__in = (t for t of type).join(",")
        date = date ? {}
        if date.from?
            params['time__gte'] = date.from
        if date.to?
            # Dates are converted to midnight, so
            # we'll have to add one
            params['time__lte'] = moment(date.to, 'YYYY-MM-DD')
                .add(1, 'day').format('YYYY-MM-DD')
        
        @filters = _.extend {}, @base_filters, params
        return (@collection.fetch
            reset: true
            data: @filters)
    
    add_item: (item) =>
        view = new ActivityView model: item, has_actor: true
        view.render()
        @$el.append view.el

    add_all_items: (coll) =>
        @$el.empty()
        coll.each @add_item

    load_more: =>
        @collection.filters.offset += @collection.filters.limit
        return (@collection.fetch
            reset: false
            data: _.clone @filters)

class @ActivityFeedControl
    constructor: (@state) ->
        @type_state = @state.sub "type"
        @kw_state = @state.sub "keyword"
        @date_state = @state.sub "date"

    feed_view: (view) => @state.on (opts={}) =>
        view.filter opts
        view.el.parent().find(".activity-feed-end").gimmesomemore ->
            $me = $ @
            $me.spin()
            view.load_more().then ({objects}) ->
                $me.spin(false)
                is_end = objects.length == 0
                $me.toggleClass "no-more-content", is_end
                return is_end
                

    scores_view: (view) => @state.on (opts={}) =>
        view.filter opts
        view.el.on "plotdaterange", (ev, date) =>
            @date_state.update date

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

    install_typeahead: (el) ->
        result_template = _.template $.trim $("#feed-filter-topic-result-template").html()
        engine = new Bloodhound
            datumTokenizer: (d) ->
                return Bloodhound.tokenizers.whitespace d.name
            queryTokenizer: Bloodhound.tokenizers.whitespace
            remote:
                url: API_PREFIX + 'keyword/?input=%QUERY'
                filter: (resp) ->
                    return resp.objects
        engine.initialize()

        args =
            minLength: 3
            highlight: true
        datasets =
            source: engine.ttAdapter()
            displayKey: (d) ->
                d.print_name
            templates:
                suggestion: (data) ->
                    return result_template data

        el.typeahead args, datasets
        el.on 'typeahead:selected', (ev, suggestion) =>
            console.log suggestion

    controls: (el) =>
        kw_state = @kw_state
        type_state = @type_state
        
        kw_state.on (value) ->
            el.find(".tag-filter-input").val(value ? "")
        el.find(".tag-filter-input").change -> kw_state.update $(@).val()

        @install_typeahead el.find(".tag-filter-input")

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
        
        filter_buttons.find(".filter-group-button").click ->
            update = {}
            grp = $(@)
            value = if grp.hasClass("active") then undefined else 1
            for btn in grp.parent().find(".filter-button")
                update[$(btn).data('feed-type')] = value
            type_state.update update
        
        date_state = @date_state
        daterange_group = el.find(".daterange-filter-group").show()
        daterange = daterange_group.find(".input-daterange")
        daterange.datepicker
            clearBtn: true
            language: "fi"
            autoclose: true
            todayHiglight: true
        
        datestr = (value) ->
            if not value?
                return undefined
            moment(value).format('YYYY-MM-DD')
        
        for myel in daterange_group.find('input')
            myel = $ myel
            sub = date_state.sub(myel.attr "name")
            myel.on "changeDate", do (sub) -> (ev) ->
                sub.update datestr ev.date
            
            sub.on do (myel) -> (value) ->
                if value?
                    value = moment(value, 'YYYY-MM-DD').toDate()
                myel.datepicker 'update', value
            
        startel = daterange_group.find "[name=start]"
        endel = daterange_group.find "[name=end]"

