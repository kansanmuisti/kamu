class @MemberActivityScoresView extends @ActivityScoresView
    initialize: (member, options) ->
        super (new MemberActivityScoresList member.get 'id'), options

$ ->
    root_el = $(document)
    relel = (selector) -> root_el.find(selector)
    tags = ({name: x[0], id: x[0].toLowerCase(), count: x[1]} for x in keyword_activity)
    tags = _.sortBy tags, (x) -> x.name
    tagcloud = $(".activity-tag-cloud")
    if tags.length > 0
        tagcloud.tag_cloud tags
    else
        tagcloud.append("<h4>Ei asiasanoitettua aktiivisuutta</h4>")
    member_activity_scores_view = new MemberActivityScoresView member,
        show_average_activity: true,
        end_date: member_activity_end_date,
        el: relel ".activity-graph"
    
    setup = new ActivityFeedControl hashstate.sub "as"
    setup.feed_view new ActivityFeedView
        el: relel ".activity-feed"
        collection: new MemberActivityList(filter: pk: member.get "id")
    setup.scores_view member_activity_scores_view
    setup.tagcloud tagcloud
    setup.controls relel ".feed-filters"
    
