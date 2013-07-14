
class @MemberActivityFeedView extends Backbone.View
    el: $("#member-activity-feed")
    initialize: (@member) ->
        _.bindAll @
        @collection = new MemberActivityList()
        @collection.bind 'add', @add_item
        @collection.bind 'reset', @add_all_items
        @collection.fetch
            data:
                member: @member.get 'id'
                limit: 20

    add_item: (item) ->
        view = new MemberActivityView model: item
        @$el.append view.render().el

    add_all_items: (coll) ->
        @el.empty()
        for item in coll
            @add_item item
