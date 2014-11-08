# A hopefully corner-caseless infinity scroll plugin
# in 13 lines. Requires jquery.appear.js.
$.fn.extend
    gimmesomemore: (giveittomebaby) ->
        me = @
        satisfyme = ->
            giveittomebaby.call(me).done (nomoreplz) ->
                return if nomoreplz
                $.force_appear()
        
        @on "appear", ->
            satisfyme()
        
        @appear force_process: true

