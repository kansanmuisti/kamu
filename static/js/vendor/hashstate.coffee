get_path_val = (object, var_path) ->
    for part in var_path
        if part not of object
            return undefined
        object = object[part]
    return object

deep_extend = (target, update) ->
    for subname, value of update
        if not value?
            delete target[subname]
            continue
        if not _.isObject value
            target[subname] = value
            continue
        if not target[subname]?
            target[subname] = {}
        deep_extend target[subname], value

class StateChangeBinder
    constructor: (@state={}) ->
        @listeners = []

    on: (var_path, handler) =>
        @listeners.push [var_path, handler]
        handler get_path_val(@state, var_path), undefined
    
    resetState: (new_state) =>
        old_state = @state
        @state = new_state
        for [var_path, handler] in @listeners
            new_val = get_path_val @state, var_path
            old_val = get_path_val old_state, var_path
            if _.isEqual new_val, old_val
                continue
            # TODO: Don't stop processing on exception
            handler(new_val, old_val)

# TODO: Hack for old browsers?
get_state_string = ->
    return window.location.search[1..]
    
set_state_string = (new_hash, history=false) ->
    if new_hash
        new_hash = '?' + new_hash
    else
        # History.js (or HTML state API?) won't change
        # the state at all if we give in an empty string, so we'll
        # have to resort to having an empty question mark
        new_hash = '?'
    new_state = [History.getState().data, document.title, new_hash]
    if history
        History.pushState new_state...
    else
        History.replaceState new_state...

# TODO: Track (and signal) "pending" states
class HashState
    constructor: ->
        @binder = new StateChangeBinder
        
        History.Adapter.bind window, "statechange", =>
            @_onHash get_state_string()
        @_onHash get_state_string()
    
    _onHash: (new_hash) =>
        @binder.resetState sanedeparam new_hash
    
    update: (changes, history=false) =>
        # TODO: Not necessarily needed
        new_state = JSON.parse JSON.stringify @binder.state
        deep_extend new_state, changes
        new_hash = saneparam new_state
        set_state_string new_hash, history
    
    _onChild: (var_path, handler) =>
        @binder.on var_path, handler
    
    get: (var_path=[]) =>
        get_path_val @binder.state, var_path

    sub: (varname) => new SubState @, varname

class SubState
    constructor: (@parent, @varname) ->
    
    update: (changes, history=false) =>
        subchanges = {}
        subchanges[@varname] = changes
        @parent.update subchanges, history

    get: (var_path=[]) =>
        if _.isString var_path
                var_path = [var_path]
        var_path.unshift(@varname)
        @parent.get var_path

    on: (handler) =>
        @parent._onChild [@varname], handler

    _onChild: (var_path, handler) =>
        var_path.unshift(@varname)
        @parent._onChild var_path, handler
    
    sub: (varname) -> new SubState @, varname

if not @hashstate?
    @hashstate = new HashState
