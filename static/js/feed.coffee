class @MemberActivityView extends Backbone.View
    tagName: 'div'

    initialize: ->

    render: ->
        obj = @model.toJSON()
        html = _.template $("#activity-item-template").html(), obj
        @$el.html html
        return @
