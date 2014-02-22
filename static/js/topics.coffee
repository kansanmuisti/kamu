class FeaturedTopicListView extends Backbone.View
    el: '.featured-issues'
    template: _.template $.trim $("#featured-topics-template").html()
    events:
        'click .nav-tabs li a': 'select_tab_click'

    initialize: (opts) ->
        @tabs = []
        for tab in opts.tabs
            t =
                id: tab.id
                name: tab.name
                active: false
                list: new KeywordList

            if tab.data
                t.list.reset tab.data

            t.list.filters['activity'] = true
            if tab.filters
                _.extend t.list.filters, tab.filters
            @tabs.push t

    render: ->
        @$el.html @template {tabs: @tabs}
        for tab in @tabs
            tab.header_el = @$el.find($("a[data-tab='#{tab.id}']")).parent()
            tab.pane_el = @$el.find($(".tab-pane[data-tab='#{tab.id}']"))
        @select_tab @tabs[0]

    render_tags: =>
        tagcloud_el = $('<div class="tagcloud tagcloud-navi" />')
        #tagcloud_el = @active_tab.pane_el.find(".tagcloud")
        #tagcloud_el.empty()
        tags = []
        @active_tab.list.each (kw) ->
            tag =
                name: kw.get('name')
                id: kw.get('id')
                count: kw.get('activity_score')
                url: kw.get_view_url()

            tags.push tag
        tags = _.sortBy tags, (t) -> t.name
        tagcloud_el.tag_cloud tags

        ul = @$el.find('.tab-pane ul')
        if false and ul.length
            ul.quicksand tagcloud_el.find('li')
        else
            @$el.find('.tab-pane').empty().append tagcloud_el

    select_tab: (new_tab) ->
        if new_tab.active
            return
        for tab in @tabs
            tab.header_el.removeClass "active"
            tab.pane_el.removeClass "active"
        new_tab.pane_el.addClass "active"
        new_tab.header_el.addClass "active"
        
        pane = @$el.find('.tab-pane')
        pane.empty().spin()
        @active_tab = new_tab
        if new_tab.list.length
            @render_tags()
        else
            new_tab.list.fetch
                success: @render_tags

    select_tab_click: (ev) ->
        el = $(ev.currentTarget)
        ev.preventDefault()
        tab_id = el.data 'tab'
        for tab in @tabs
            if tab.id == tab_id
                @select_tab tab
                break

render_tags = (el, data) ->

#render_tags $("#recent_tags"), recent_topics_json
#render_tags $("#term_tags"), term_topics_json
#render_tags $("#alltime_tags"), all_time_topics_json

featured_list_view = new FeaturedTopicListView tabs: FEATURED_TABS
featured_list_view.render()
