class @MemberActivityScoresView extends Backbone.View
    initialize: (options) ->
        @member = options.member
        end_date = options.end_date
        @collection = new MemberActivityScoresList @member.get 'id'
        @collection.bind 'reset', @add_all_items

        time = new Date(end_date)
        year = time.getFullYear()
        month = time.getMonth()
        @start_time = new Date(year - 2, month + 1, 1)
        start_time_str = @start_time.getFullYear() + "-" +  \
                          (@start_time.getMonth() + 1) + "-" + \
                          @start_time.getDate()

        time =  new Date(new Date(year, month + 1, 1).getTime() - 1)
        year = time.getFullYear()
        month = time.getMonth()
        day = time.getDate()
        @end_time = new Date(year, month, day)
        end_time_str = @end_time.getFullYear() + "-" + \
                       (@end_time.getMonth() + 1) + "-" + \
                       @end_time.getDate()

        resolution = 'month'
        @avg_bin_score = activity_daily_avg * 30

        params =
            resolution: resolution
            since: start_time_str
            until: end_time_str
            limit: 0
        @collection.fetch
            reset: true
            data: params

    add_all_items: (coll) =>
        @graph = new ActivityScoresView el:@el,                     \
                                        start_time: @start_time,    \
                                        end_time: @end_time,        \
                                        scores:coll,                \
                                        avg_bin_score:@avg_bin_score



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
            @user_filters['type__type'] = type
        else
            delete @user_filters['type__type']
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
$("#member-tag-cloud").tag_cloud tags

feed_view = new MemberActivityFeedView member

$("#member-tag-cloud li a").click (ev) ->
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
