class @Member extends Backbone.Tastypie.Model
    URL_PREFIX: '/member/'
    url: -> API_PREFIX + "member/#{@get('id')}/"
    get_view_url: -> "#{@URL_PREFIX}#{@get('url_name')}/"

class @MemberList extends Backbone.Tastypie.Collection
    url: API_PREFIX + 'member/'
    model: Member

class @MemberActivity extends Backbone.Tastypie.Model

class @MemberActivityList extends Backbone.Tastypie.Collection
    url: API_PREFIX + 'member_activity/'
    model: MemberActivity
