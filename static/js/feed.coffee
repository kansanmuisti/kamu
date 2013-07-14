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

    process_summary: (text) ->
        # TODO: Twitter processing
        # Wrap text in <p> tags
        p_list = text.split '\n'
        p_list = ("<p>#{p}</p>" for p in p_list)
        return p_list.join('\n')

    render: ->
        obj = @model.toJSON()
        act = ACTIVITIES[obj.type]
        obj.action = act.action
        obj.icon = act.icon
        obj.time_ago = moment(obj.time).fromNow()
        obj.target.text = @process_summary obj.target.text
        html = _.template $("#activity-item-template").html(), obj
        @$el.html html
        @$el.find('.summary').expander
            slicePoint: 350

        return @
