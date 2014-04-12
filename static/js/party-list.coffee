class PartyListView extends Backbone.View
    el: $('div.party-list')
    el_gov: $('ul.party-list-government')
    el_oppo: $('ul.party-list-opposition')

    render: ->
        @collection.forEach @render_one, @
        return @

    render_one: (party) ->
        if party.get "governing_now"
            el = @el_gov
        else
            el = @el_oppo
        party_view = new PartyListItemView
            model: party
            # Directly render into the container ul on the Django template
            # Will this break any event listeners?
            el: el
        party_view.render().el

    _calculate_stats: ->
        stats = (m) -> m.attributes.stats
        max_score = window.ACTIVITY_BAR_CAP
        for m in @collection.models
            s = stats m
            s.activity_per_day = s.recent_activity/s.activity_days_included
            s.activity_ranking = s.activity_per_day/max_score*100
            if s.activity_ranking > 100
                s.activity_ranking = 100
    
    initialize: ->
        @collection = new PartyList
        @collection.comparator = (model) -> return -model.get('member_count')
        # This gets triggered when the content has fetch'ed from JSON
        @listenTo @collection, "reset", @_calculate_stats
        @listenTo @collection, "reset", @render
        @collection.fetch
            reset: true
            data:
                stats: true

class @PartyListItemView extends Backbone.View
    template: _.template $('#party-list-item-template').html()

    render: ->
        template_variables = @model.toJSON()
        # This is a view-specific transformation, would seem out of place in model
        if template_variables.governing_now
            template_variables.party_governing_status = "party-government"
        else
            template_variables.party_governing_status = "party-opposition"
        template_variables.view_url = @model.get_view_url()
        # Appending not a good idea?
        @$el.append @template template_variables
        return @

# Initialize the page contents
@party_list_view = new PartyListView
