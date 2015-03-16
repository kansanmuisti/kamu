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
                data.image_url = null
                if data.object_type == 'member'
                    obj = new Member data
                    data.view_url = obj.get_view_url()
                    data.image_url = obj.get_portrait_thumbnail 48
                    data.text = obj.get 'print_name'
                else if data.object_type == 'keyword'
                    obj = new Keyword data
                    data.view_url = obj.get_view_url()
                    data.text = obj.get 'name'
                else if data.object_type == 'memberactivity'
                    obj = new MemberActivity data
                    target = obj.get('target')
                    data.view_url = target.url
                    data.text = "#{target.name}: #{target.subject}"
                    console.log data
                return result_template data

    $("#main-search").typeahead args, datasets

search_handler = (ev) ->
    ev.preventDefault()
    query = $.trim $("#main-search").val()
    window.location = URL_CONFIG['search'] + '?as.q=' + query

$ ->
    install_typeahead()
    $("#main-search-form").on 'submit', search_handler
