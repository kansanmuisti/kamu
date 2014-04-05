class MostActiveMembersView extends Backbone.View
    el: ".most-active-members ul"
    template: _.template $.trim($("#most-active-mps-item").html())
    initialize: (options) ->
        @collection = new MemberList()
        @collection.bind 'reset', @add_all_items
        @params =
            order_by: '-activity_score'
            activity_since: 'month'
            limit: 10
        @collection.fetch
            reset: true
            data: @params
    add_all_items: =>
        max_score = ACTIVITY_BAR_CAP
        @$el.empty()
        @collection.each (model) =>
            data = model.toJSON()
            data.thumbnail_url = model.get_portrait_thumbnail 128
            score = data.activity_score / data.activity_days_included
            data.activity_percentage = score * 100.0 / max_score
            el = $(@template data)
            @$el.append el

view = new MostActiveMembersView()
