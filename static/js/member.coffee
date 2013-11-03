class @MemberActivityScoresView extends Backbone.View
    initialize: (options) ->
        @member = options.member
        @collection = new MemberActivityScoresList @member.get 'id'
        @collection.bind 'reset', @add_all_items

        time = new Date()
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
                                        scores:coll

class @MemberActivityFeedView extends Backbone.View
    el: ".activity-feed"
    initialize: (@member) ->
        @collection = new MemberActivityList()
        @collection.bind 'add', @add_item
        @collection.bind 'reset', @add_all_items
        @base_filters =
            member: @member.get 'id'
            limit: 20
        @filter()

    filter: (filters) ->
        params = _.clone @base_filters
        if filters
            _.extend params, filters
        @collection.fetch
            reset: true
            data: params

    filter_keyword: (kw) ->
        @filter
            keyword: kw

    add_item: (item) =>
        view = new ActivityView model: item, has_actor: false
        view.render()
        @$el.append view.el

    add_all_items: (coll) =>
        @$el.empty()
        coll.each @add_item

party_list = new PartyList party_json
