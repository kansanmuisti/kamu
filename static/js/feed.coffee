class @MemberActivityView extends Backbone.View
    tagName: 'div'

    initialize: ->
        _.bindAll @
    render: ->
        obj = @model.toJSON()
        html = _.template $("#activity-item-template").html(), obj
        @$el.html html
        return @
