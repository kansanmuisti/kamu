class @PartyActivityScoresView extends @ActivityScoresView
    initialize: (party, options) ->
        super (new PartyActivityScoresList party.get 'abbreviation'), options


