class @PartyActivityScoresView extends @ActivityScoresView
    initialize: (party, options) ->
        super (new PartyActivityScoresList party.get 'abbreviation'), options

class MemberListItemView extends Backbone.View
    initialize: ->
        @template = _.template $("#member-list-item-template").html()

    render: ->
        template_variables = @model.toJSON()
        # The number of columns in party MP list
        template_variables.columns = 2
        html = @template template_variables
        return html

class @MemberListView extends Backbone.View
    el: $("ul.member-list")

    initialize: ->
        @collection = new MemberList
        @listenTo @collection, "reset", @render
        @collection.reset party_list_json

    # Replace this with code from member-list.coffee, when it
    # has been factored out
    _calculate_stats: ->
        stats = (m) -> m.attributes.stats
        max_score = _.max @collection.models.map (m) ->
            stats(m).recent_activity
        for m in @collection.models
            s = stats m
            s.activity_ranking = s.recent_activity/max_score

    render: ->
        @_calculate_stats()

        for member in @collection.models
            item_view = new MemberListItemView
                model: member
            html = item_view.render()
            @$el.append(html)
        card_elements = $(".member-list")
        card_elements.find(".activity-ranking-statistics-bar").show()