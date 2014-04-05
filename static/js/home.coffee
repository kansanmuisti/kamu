class MostActiveMembersView extends Backbone.View
    el: '.most-active-members ul'
    template: _.template $.trim($('#most-active-mps-item').html())
    initialize: (options) ->
        @collection = new MemberList()
        @collection.bind 'reset', @add_all_items
        params =
            order_by: '-activity_score'
            activity_since: '2months'
            limit: 10
        @collection.fetch
            reset: true
            data: params
    add_all_items: =>
        max_score = ACTIVITY_BAR_CAP
        @$el.empty()
        @collection.each (model) =>
            data = model.toJSON()
            data.thumbnail_url = model.get_portrait_thumbnail 128
            score = data.activity_score / data.activity_days_included
            data.activity_percentage = score * 100.0 / max_score
            if data.activity_percentage > 100
                data.activity_percentage = 100
            el = $(@template data)
            @$el.append el

members_view = new MostActiveMembersView()

class MostActivePartiesView extends Backbone.View
    el: 'ul.highlight-parties'
    template: _.template $.trim($('#most-active-parties-item').html())
    initialize: (options) ->
        @collection = new PartyList()
        @collection.bind 'reset', @add_all_items
        params =
            activity_since: '2months'
            stats: 'true'
            recent_keywords: 'true'
        @collection.fetch
            reset: true
            data: params
    add_all_items: =>
        max_score = ACTIVITY_BAR_CAP
        @$el.empty()
        sorted = @collection.sortBy (x) -> x.get 'name'
        _.each sorted, (model) =>
            data = model.toJSON()
            data.thumbnail_url = model.get_logo_thumbnail 48, 48
            score = data.stats.recent_activity / data.stats.activity_days_included
            kw_list = []
            for kw in data.recent_keywords[0..2]
                obj = new Keyword kw
                kw_list.push obj.toJSON()
            data.recent_keywords = kw_list
            data.activity_percentage = score * 100.0 / max_score
            if data.activity_percentage > 100
                data.activity_percentage = 100
            el = $(@template data)
            @$el.append el

parties_view = new MostActivePartiesView()
