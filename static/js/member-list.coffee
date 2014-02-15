class MemberListSortButtonsView extends Backbone.View
    el: ".member-list-sort-buttons"
    template: _.template $.trim $("#member-list-sort-button-template").html()

    initialize: ->
        @listenTo member_list_view, 'sort-changed', @sort_changed

    events:
        'click button': 'handle_sort_button'

    handle_sort_button: (ev) ->
        btn = $(ev.currentTarget)
        ascending = true
        if btn.hasClass('active') and btn.hasClass('ascending')
            ascending = false

        field = $(btn).data "col"
        member_list_view.set_sort_order field, ascending

    sort_changed: (field, ascending) ->
        @$el.find('button').removeClass('active').removeClass('ascending').find('i').remove()
        active_btn = @$el.find("[data-col='#{field.id}']")
        active_btn.addClass 'active'
        if ascending
            icon = 'arrow-up'
            active_btn.addClass 'ascending'
        else
            icon = 'arrow-down'
        active_btn.append $("<i class='typcn typcn-#{icon}'></i>")

    render: ->
        @$el.empty()
        for f in MEMBER_LIST_FIELDS
            button_el = $(@template f)
            if member_list_view.active_sort_field.id == f.id
                button_el.addClass 'active'
            @$el.append button_el
        return @

class MemberListItemView extends Backbone.View
    template: _.template $("#member-list-item-template").html()

    render: (sort_order) ->
        attr = @model.toJSON()
        attr.party = @model.get_party(party_list)
        attr.sort_order = sort_order.id
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
        @index.field "titles"
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
                limit: 500
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
        attrsort = (field) ->
            (aw, bw) ->
                a = aw.model.attributes[field]
                b = bw.model.attributes[field]
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
            age: attrsort('age')

        @_sort_fields = []
        for field in MEMBER_LIST_FIELDS
            # Copy the original object
            f = $.extend {}, field
            f.sort_func = @_sort_funcs[f.id]
            @_sort_fields.push f

        @_raw_sort_func = null
        @sort_order = 1
        @sort_func = (a, b) =>
            @sort_order*@_raw_sort_func(a, b)
        
        # Just to have something in the sort order,
        # this will be overriden once we get data
        @set_sort_order "recent_activity"

    _calculate_rankings: (collection) =>
        activity_scores = (model.attributes.stats['recent_activity'] \
            for model in collection.models)
        activity_scores = _.sortBy activity_scores, (x) -> x
        percentile = (v) ->
            activity_scores.indexOf(v)/(activity_scores.length-1)
        for model in collection.models
            stats = model.attributes.stats
            stats['activity_ranking'] = percentile stats['recent_activity']

    set_sort_order: (field, ascending=true) =>
            for f in @_sort_fields
                if f.id == field
                    break
            @active_sort_field = f

            func = f.sort_func
            if ascending
                @sort_order = -1
            else
                @sort_order = 1

            @_raw_sort_func = func
            @_filter_listing(field)

            @trigger 'sort-changed', f, ascending

    _update_search_hint: (col) =>
        i = Math.floor(Math.random()*(col.models.length))
        model = col.models[i]
        a = model.attributes
        hint = a.given_names.split(" ", 1)[0].split('-', 1)[0].toLowerCase() + " " +
            model.get_party(party_list).get('name').toLowerCase()[..2] + " " +
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
            hit.render(@active_sort_field.id)
            @$el.append hit.el
        
        css_class = switch @active_sort_field.id
            when 'attendance' then '.attendance-statistics-bar'
            when 'party_agree' then '.party-agree-statistics-bar'
            when 'party_agree' then '.party-agree-statistics-bar'
            else '.activity-ranking-statistics-bar'
        
        @$el.find(css_class).show()

    _process_children: (collection) =>
        @spinner_el.spin false
        for model in collection.models
            item_view = new MemberListItemView model: model
            @children[model.id] = item_view
            party = model.get_party party_list

            titles = []
            if model.is_minister()
                titles.push MINISTER_TRANSLATION

            @index.add
                id: model.id
                name: model.get('name')
                party: party.get('name')
                party_short: party.get('abbreviation')
                district: model.attributes.district_name
                titles: titles.join(', ')

    render: ->
        @_calculate_rankings @collection
        @_process_children @collection
        @_update_search_hint @collection
        @_filter_listing()
        @set_sort_order "recent_activity", false

member_list_view = new MemberListView
sort_buttons_view = new MemberListSortButtonsView
sort_buttons_view.render()
party_list = new PartyList party_json
