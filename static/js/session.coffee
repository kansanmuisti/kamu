# Hacks to work around hacks :(
fix_undefineds = (obj) ->
    if not _.isObject obj
        return obj
    newobj = {}
    for k, v of obj
        continue if typeof v == "undefined"
        newobj[k] = fix_undefineds v
    return newobj

apiurl = (path, args={}) ->
    url = "/api/v1/#{path}"
    args = fix_undefineds args
    if not _.isEmpty args
        url += "?"+$.param args
    return url

SESSIONS_PER_REQUEST = 1
# Gotta love Tastypie
ALMOST_INFINITY=1000

last_date_visible = undefined
session_template = _.template $("#plenary-session-template").html()
session_item_template = _.template $("#plenary-session-item-template").html()

render_session_item = (item) ->
    el = $ session_item_template item
    el.find("> ul").append item.subitems.map render_session_item
    return el

render_sessions = (sessions) ->
    container = $("#session-item-list")
    for session in sessions
        session.date_str = moment(session.date).format 'DD.MM.YYYY'
        el = $ session_template session
        el.find('> ul').append session.session_items.map render_session_item
        container.append el
        last_date_visible = session.date

fetch_sessions = (date_limit=undefined, offset=0, limit=SESSIONS_PER_REQUEST) ->
    # I really shouldn't have to do this on the client side!
    # Somebody else can make yet another dehydrate hack if they are worried
    # about performance. I don't care anymore. Damn you Tastypie!
    # Actually if there was a sane backend and a sane data binder, I wouldn't
    # have to do any of this. -Jami
    
    # Corresponds approximatedly to PlenarySessionItem.get_short_id
    # in the backend. Behind these hacks there's a long and sad story
    # with themes like C winning over Lisp and Unix over Plan9.
    hacky_session_item_url = (model) ->
        url = "/session/#{model.session.url_name}/#{model.number}/"
        if model.sub_number > 0
            url += "#{model.sub_number}/"
        return url
    
    hacky_session_item_description = (item) ->
        return item.sub_description ? item.description
    
    populate_session = (session) ->
        $.getJSON(apiurl "plenary_session_item/",
            plenary_session: session.id
            limit: ALMOST_INFINITY)
        .then ({meta, objects}) ->
            toplevel = []
            toplevel_index = {}
            non_toplevel = []
            for item in objects
                item.session = session
                item.view_url = hacky_session_item_url item
                item.default_description = hacky_session_item_description item
                item.subitems = []
                if item.sub_number > 0
                    non_toplevel.push item
                    continue
                toplevel.push item
                toplevel_index[item.number] = item

            for item in non_toplevel
                toplevel_index[item.number].subitems.push item

            session.session_items = toplevel
                
            return session
            

    $.getJSON(apiurl "plenary_session/",
        limit: limit
        offset: offset
        date__lt: date_limit)
    .then ({meta, objects}) ->
        $.when(objects.map(populate_session)...)
        .then (args...) -> args
        

$("#session-item-list-end").gimmesomemore ->
    $me = $ @
    $me.spin()
    fetch_sessions(last_date_visible)
    .then (sessions) ->
        render_sessions (sessions)
        $me.spin(false)
        is_end = sessions.length == 0
        $me.toggleClass "no-more-content", is_end
        return is_end
