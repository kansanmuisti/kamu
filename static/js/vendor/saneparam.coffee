is_iterable = (obj) ->
    _.isArray(obj) or _.isObject(obj)

do_saneparam = (obj, prefix, result=[]) ->
    for key, value of obj
        if not value
            continue
        enckey = encodeURIComponent key
        if _.isArray value
            throw new Error "Serializing arrays is not currently supported"
        if not _.isObject value
            result.push "#{prefix}#{enckey}=#{encodeURIComponent value}"
        else
            do_saneparam value, "#{prefix}#{enckey}.", result
    return result

@saneparam = (obj) ->
    result = do_saneparam(obj, '').join '&'
    return result

@sanedeparam = (qs) ->
    out = {}
    for part in qs.split '&'
        obj = out
        [name, value...] = part.split '='
        if name == ""
            continue
        value = value.join '='
        [nss..., name] = name.split('.').map decodeURIComponent
        for ns in nss
            if ns not of obj
                obj[ns] = {}
            obj = obj[ns]
        obj[name] = decodeURIComponent value
    return out

