is_iterable = (obj) ->
    _.isArray(obj) or _.isObject(obj)

do_saneparam = (obj, prefix) ->
    result = []
    for key, value of obj
        enckey = encodeURIComponent key
        if not is_iterable(value)
            result.push "#{prefix}#{enckey}=#{encodeURIComponent value}"
        else
            result.push do_saneparam value, "#{prefix}#{enckey}."
    return result

@saneparam = (obj) ->
    return do_saneparam(obj, '').join('&')

@sanedeparam = (qs) ->
    out = {}
    for part in qs.split '&'
        obj = out
        [name, value...] = part.split '='
        value = value.join '='
        [nss..., name] = name.split('.').map decodeURIComponent
        for ns in nss
            if ns not of obj
                obj[ns] = {}
            obj = obj[ns]
        obj[name] = decodeURIComponent value
    return out

