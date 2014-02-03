class @PartyActivityScoresView extends @ActivityScoresView
    initialize: (party, options) ->
        super (new PartyActivityScoresList party.get 'name'), options

class MemberListItemView extends Backbone.View
    template: _.template $("#member-list-item-template").html()

    render: ->
        template_variables = @model.toJSON()
        html = @template template_variables
        return html

class @MemberListView extends Backbone.View
    el: $("ul.member-list")

    initialize: ->
        @collection = new MemberList
        @listenTo @collection, "reset", @render
        @collection.reset party_list_json

    render: ->
        for member in @collection.models
            item_view = new MemberListItemView
                model: member
            html = item_view.render()
            @$el.append(html)
