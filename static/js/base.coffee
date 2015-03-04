install_typeahead = ->
    result_template = _.template $.trim $("#main-search-result").html()
    engine = new Bloodhound
        datumTokenizer: (d) ->
            return Bloodhound.tokenizers.whitespace d.name
        queryTokenizer: Bloodhound.tokenizers.whitespace
        remote:
            url: API_PREFIX + 'search/?input=%QUERY'
            filter: (resp) ->
                return resp.objects
    engine.initialize()

    args = 
        minLength: 3
        highlight: true
    datasets =
        source: engine.ttAdapter()
        displayKey: (d) ->
            d.print_name
        templates:
            suggestion: (data) ->
                obj = new Member data
                data.view_url = obj.get_view_url()
                data.image_url = obj.get_portrait_thumbnail 48
                data.text = obj.get 'print_name'
                return result_template data

    $("#main-search").typeahead args, datasets

search_handler = (ev) ->
    ev.preventDefault()
    query = $.trim $("#main-search").val()
    window.location = URL_CONFIG['search'] + '?q=' + query

$ ->
    install_typeahead()
    $("#main-search-form").on 'submit', search_handler
