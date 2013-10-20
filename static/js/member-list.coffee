@_share_as_stars = (n, max=5) ->
    str = ""
    semistars = Math.round n*2*max
    fullstars = Math.floor semistars/2.0
    halfstars = semistars%2
    for i in [0...fullstars]
        str += '<i class="icon-star media-object" style="font-size: 12px"></i>'
    if halfstars
        str += '<i class="icon-star-half-empty media-object" style="font-size: 12px"></i>'
        i += 1
    while i < max
        str += '<i class="icon-star-empty media-object" style="font-size: 12px"></i>'
        i += 1
    return str

class MemberListItemView extends Backbone.View
    template: _.template $("#member-list-item-template").html()

    render: ->
        attr = @model.toJSON()
        attr.party = @model.get_party(party_list)
        html = $($.trim(@template attr))
        @$el = html
        @el = @$el[0]
        return @

class MemberListView extends Backbone.View
    el: "ul.member-list"
    spinner_el: ".spinner-container"
    search_el: "main .text-search"

    initialize: ->
        @spinner_el = $(@spinner_el)
        @spinner_el.spin top: 0

        @children = {}

        @collection = new MemberList
        @listenTo @collection, "add", @append_item
        @listenTo @collection, "reset", @render

        @index = new lunr.Index
        @index.field "name"
        @index.field "party"
        @index.field "district"
        @index.field "party_short"
        @index.ref "id"

        @search_el = $(@search_el)
        @search_el.input @_filter_listing

        @_setup_sort()

        @collection.fetch
            reset: true
            data:
                thumbnail_dim: "104x156"
                current: true
                stats: true
                limit: 0
            processData: true

    _setup_sort: =>
        namesort = (a, b) -> a.model.attributes['name'].localeCompare b.model.attributes['name']
        statsort = (field) ->
            (aw, bw) ->
                a = aw.model.attributes.stats[field]
                b = bw.model.attributes.stats[field]
                if a == b
                    return namesort(aw, bw)
                if a > b
                    return -1
                else
                    return 1

        @_sort_funcs =
            name: namesort
            recent_activity: statsort('recent_activity')
            attendance: statsort('attendance')
            party_agree: statsort('party_agree')
            session_agree: statsort('party_agree')
            term_count: statsort('term_count')

        @_raw_sort_func = null
        @sort_order = 1
        @sort_func = (a, b) =>
            @sort_order*@_raw_sort_func(a, b)

        # Just to have something in the sort order,
        # this will be overriden once we get data
        @_set_sort_order "name"

        $(".member-list-sort-buttons button").click (ev) =>
            console.log "click"
            btn = ev.currentTarget
            field = $(btn).data "col"
            @_set_sort_order field

    _calculate_rankings: (collection) =>
        activity_scores = (model.attributes.stats['recent_activity'] \
            for model in collection.models)
        activity_scores = _.sortBy activity_scores, (x) -> x
        percentile = (v) ->
            activity_scores.indexOf(v)/(activity_scores.length-1)
        for model in collection.models
            stats = model.attributes.stats
            stats['activity_ranking'] = percentile stats['recent_activity']

    _set_sort_order: (field, toggle_order=true) =>
            func = @_sort_funcs[field]
            if toggle_order and func == @_raw_sort_func
                @sort_order *= -1
            # This is probably more intuitive and allows
            # for nicer comparisons
            #else
            #    @sort_order = 1

            $("#member-sort-buttons button .sort-order").remove()
            btn = $("#member-sort-buttons button[data-col='#{field}']")
            order_widget = $ '<div class="sort-order"></div>'
            if @sort_order > 0
                order_widget.addClass "sort-order-asc"
            else
                order_widget.addClass "sort-order-desc"

            btn.append order_widget

            $("#member-list .member-stats > li").hide()
            $("#member-list .member-stats > li.#{field}").show()

            @_raw_sort_func = func
            @_filter_listing()

    _update_search_hint: (col) =>
        i = Math.floor(Math.random()*(col.models.length))
        model = col.models[i]
        a = model.attributes
        hint = a.given_names.split(" ", 1)[0].split('-', 1)[0].toLowerCase() + " " +
            model.get_party(party_list).get('full_name').toLowerCase()[..2] + " " +
            a.district_name.toLowerCase()[..3]

        #$el = @search_el
        #$el.attr "placeholder", $el.attr("placeholder") + hint

    _filter_listing: =>
        @$el.empty()
        query = @search_el.val()
        if not query
            result = (@children[key] for key of @children)
        else
            result = (@children[hit.ref] for hit in @index.search query)

        result.sort @sort_func

        for hit in result
            @$el.append hit.el

    _process_children: (collection) =>
        @spinner_el.spin false
        for model in collection.models
            item_view = new MemberListItemView model: model
            item_view.render()
            @children[model.id] = item_view
            party = model.get_party party_list
            @index.add
                id: model.id
                name: model.get('name')
                party: party.get('full_name')
                party_short: party.get('name')
                district: model.attributes.district_name

    render: ->
        @_calculate_rankings @collection
        @_process_children @collection
        @_update_search_hint @collection
        @_filter_listing()
        @_set_sort_order "recent_activity", false


member_list_view = new MemberListView
party_list = new PartyList party_json
