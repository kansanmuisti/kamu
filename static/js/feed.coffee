make_time_string = (time) ->
    m = moment time
    now = moment()
    if now.diff(m, 'hours') < 24
        return m.fromNow()
    else if now.year() == m.year()
        f = moment.langData()._longDateFormat['LL']
        format = f.replace ' YYYY', ''
    else
        format = 'LL'
    return m.format format

class @MemberActivityView extends Backbone.View
    tagName: 'li'
    className: 'activity-item single-actor'
    template: _.template $.trim($("#activity-item-template").html())

    initialize: ->

    process_summary: (text) ->
        # TODO: Twitter processing
        # Wrap text in <p> tags
        p_list = text.split '\n'
        p_list = ("<p>#{p}</p>" for p in p_list)
        return p_list.join('\n')

    render: ->
        obj = @model.toJSON()
        act = FEED_ACTIONS[obj.type]
        # If we have a target-specific action string, use it.
        if act.action_with_target and obj.target.type of act.action_with_target
            obj.action = act.action_with_target[obj.target.type]
        else
            obj.action = act.action
        obj.icon = act.icon
        obj.time_str = make_time_string obj.time
        obj.target.text = @process_summary obj.target.text
        html = @template obj
        @$el.html html
        @$el.find('.summary').expander
            slicePoint: 350
            hasBlocks: true

        return @
