class @Member extends Backbone.Tastypie.Model
    URL_PREFIX: '/member/'
    get_view_url: -> "#{@URL_PREFIX}#{@attributes.url_name}/"

class @MemberList extends Backbone.Tastypie.Collection
    url: API_PREFIX + 'member/'
    model: Member
