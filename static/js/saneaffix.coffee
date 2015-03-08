@saneaffix_y = (myel, myclass="affix-always") -> do (myel) -> # Create a new scope
    anchor = $ '<div class="affix-anchor">'
    placeholder = $ '<div class="affix-placeholder">'
    myel.after placeholder
    myel.before anchor
    myel.addClass myclass
    hack_sizes = ->
        myel.outerWidth(anchor.width())
        placeholder.height myel.outerHeight(true)
    
    myel.affix
        offset:
            top: ->
                anchor.offset().top
    
    myel.on "affixed.bs.affix", hack_sizes
    $(window).resize hack_sizes

