ACTIVITIES =
    TW:
        action: 'lähetti Tweetin'
        icon: 'twitter'
    FB:
        action: 'teki Facebook-päivityksen'
        icon: 'facebook'
    ST:
        action: 'käytti täysistuntopuheenvuoron'
        icon: 'comment-alt'
    SI:
        action: 'allekirjoitti aloitteen'
        icon: 'pencil'
    IN:
        action: 'teki lakialoitteen'
        icon: 'lightbulb'
    WQ:
        action: 'jätti kirjallisen kysymyksen'
        icon: 'question'

class @MemberActivityView extends Backbone.View
    tagName: 'li'
    className: 'activity'

    initialize: ->

    render: ->
        obj = @model.toJSON()
        act = ACTIVITIES[obj.type]
        obj.action = act.action
        obj.icon = act.icon
        obj.time_ago = moment(obj.time).fromNow()
        html = _.template $("#activity-item-template").html(), obj
        @$el.html html
        @$el.find('.summary').expander
            slicePoint: 350

        return @
