class FeedFilterButtonsView extends Backbone.View
    el: '.feed-filters .btn-toolbar'
    initialize: (options) ->
        @filter_groups = options.filter_groups

    render: ->
        @$el.empty()
        for group in @filter_groups
            grp_el = $('<div class="btn-group" />')
            for f in group.filters
                el = $("<button class='btn btn-small' type='button' />")
                console.log f.icon
                if f.icon
                    el.append $("<i class='typcn typcn-#{f.icon}' />")
                    el.attr 'title', f.name
                else
                    el.html f.name
                el.data 'filter-type', f.type
                if f.button_type
                    el.addClass('btn-' + f.button_type)
                grp_el.append el
            @$el.append grp_el


class TopicFeedView extends Backbone.View
    el: 'ul.activity-feed'
    initialize: (opts) ->
        @keyword = opts.keyword
        @collection = new KeywordActivityList
        @collection.filters['keyword'] = @keyword.get 'id'
        @collection.filters['activity__type__in'] = 'IN,GB,WQ' # FIXME: do not hardcode
        @listenTo @collection, "add", @render_one
        @collection.fetch()

    render_one: (model) ->
        activity = new MemberActivity(model.get 'activity')
        view = new ActivityView model: activity, has_actor: true
        view.render()
        @$el.append view.$el

keyword = new Keyword keyword_json
feed_view = new TopicFeedView keyword: keyword
feed_filters = [
    {name: "parliament", filters: FEED_FILTERS.parliament},
    {name: "all", filters: [FEED_FILTER_ALL]}
]
feed_filter_buttons = new FeedFilterButtonsView filter_groups: feed_filters
feed_filter_buttons.render()
