# A hopefully corner-caseless infinity scroll plugin
# in 15 lines. Requires jquery.appear.js.
$.fn.extend
    gimmesomemore: (giveittomebaby) ->
        me = @
        pending = false
        satisfyme = ->
            pending = giveittomebaby.call(me).done (nomoreplz) ->
                pending = false
                return if nomoreplz
                $.force_appear()
        
        @on "appear", ->
            return if pending
            satisfyme()
        
        @appear force_process: true
