
class TopicFeedView extends Backbone.View
    el: 'ul.activity-feed'
    initialize: (opts) ->
        @keyword = opts.keyword
        @collection = new KeywordActivityList
        @collection.filters['keyword'] = @keyword.get 'id'
        @collection.filters['activity__type__in'] = 'IN,GB,WQ' # FIXME: do not hardcode
        @listenTo @collection, "add", @render_one
        @collection.fetch()

    render_one: (model) ->
        activity = new MemberActivity(model.get 'activity')
        view = new ActivityView model: activity, has_actor: true
        view.render()
        @$el.append view.$el
        console.log "render_one", activity

keyword = new Keyword keyword_json
feed_view = new TopicFeedView keyword: keyword
