make_time_string = (time) ->
    m = moment time
    now = moment()
    if now.diff(m, 'hours') < 24
        return m.fromNow()
    else if now.year() == m.year()
        f = moment.localeData()._longDateFormat['LL']
        format = f.replace ' YYYY', ''
    else
        format = 'LL'
    return m.format format

class @ActivityView extends Backbone.View
    tagName: 'li'
    className: 'activity-item'
    template: _.template $.trim($("#activity-item-template").html())

    initialize: (options) ->
        @has_actor = options.has_actor

    process_summary: (text) ->
        if @model.get('type') == 'TW'
            return twttr.txt.autoLink text
        if @model.get('type') == 'FB'
            text = text.autoLink()
        # Wrap text in <p> tags
        p_list = text.split '\n'
        p_list = ("<p>#{p}</p>" for p in p_list)
        return p_list.join('\n')

    render: ->
        obj = @model.toJSON()
        if @has_actor and obj.member
            obj.actor =
                name: "#{obj.member_info.print_name} /#{obj.member_info.party}"
                url: URL_CONFIG['member_details'].replace 'MEMBER', obj.member_info.slug
                thumbnail_url: obj.member + 'portrait/?dim=106x159'
        else
            obj.actor = null
        act = FEED_ACTIONS[obj.type]
        # If we have a target-specific action string, use it.
        if act.action_with_target and obj.target.type of act.action_with_target
            obj.action = act.action_with_target[obj.target.type]
        else
            obj.action = act.action
        obj.icon = act.icon
        obj.time_str = make_time_string obj.time
        if obj.target.text
            obj.target.text = @process_summary obj.target.text
        if obj.target.keywords
            for kw in obj.target.keywords
                kw.view_url = URL_CONFIG['topic_details'].replace('999', kw.id).replace('SLUG', kw.slug)

        html = @template obj
        @$el.html html
        @$el.find('.summary').expander
            slicePoint: 350
            hasBlocks: true

        return @
