class @MemberActivityScoresView extends Backbone.View
    initialize: (options) ->
        @member = options.member
        @collection = new MemberActivityScoresList @member.get 'id'
        @collection.bind 'reset', @add_all_items
        params =
            resolution: 'day'
            limit: 0
        @collection.fetch
            reset: true
            data: params

    add_all_items: (coll) =>
        @graph = new ActivityScoresView el:@el, scores:coll

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
