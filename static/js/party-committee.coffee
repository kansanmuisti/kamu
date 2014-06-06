class @PartyCommitteeView extends Backbone.View
    el: 'ul#committee-seat-list'
    template: _.template $('#committee-list-template').html()

    initialize: (options) ->
        @committees = {}
        @collection = new MemberList
        @listenTo @collection, "reset", @render

        params =
            party__abbreviation: options.party_abbreviation
            current: true
            # Just making this explicit, as it is very expensive
            stats: false

        @collection.fetch
            reset: true
            data: params

    gather_committee_members: (collection) ->
        for model in @collection.models
            posts = model.get "posts"
            if posts.committee? and posts.committee.length > 0
                for seat in posts.committee
                    if not @committees[seat.committee]?
                        @committees[seat.committee] = []
                    committee_seat = [seat.role, model]
                    @committees[seat.committee].push committee_seat

    translate_role: (committee_role) ->
        switch committee_role
            when "member" then MEMBER_TRANSLATION
            when "deputy-m" then DEPUTYM_TRANSLATION
            when "chairman" then CHAIRMAN_TRANSLATION
            else committee_role

    render: ->
        @gather_committee_members @collection
        for committee, seats of @committees
            members_json = []
            for seat in seats
                mj = seat[1].toJSON()
                mj.committee_role = @translate_role seat[0]
                members_json.push mj
                
            params =
                name: committee
                members: members_json
            @$el.append @template params
