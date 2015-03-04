related_tags = []
for kw_dict in keyword.get('related')[0..10]
    kw = new Keyword kw_dict
    tag =
        name: kw.get 'name'
        id: kw.get 'id'
        count: kw.get 'count'
        url: kw.get_view_url()
    related_tags.push tag

related_tags = _.sortBy related_tags, (t) -> t.name
$(".feature-tagcloud .tagcloud").tag_cloud related_tags

#
# Most active MPs and parties
#
most_active = keyword.get 'most_active'
$ul = $(".most-active-parties ol")
template = _.template $.trim $("#most-active-party-template").html()
max_score = _.max(party.score for party in most_active.parties)
for p in most_active.parties[0..5]
    party = new Party p
    dict = party.toJSON()
    dict.thumbnail_url = party.get_logo_thumbnail(64, 64)
    # Better scaling would be a good thing
    dict.party_activity_percentage = p.score / max_score * 100
    $ul.append $(template(dict))

$ul = $(".most-active-members ol")
template = _.template $.trim $("#most-active-member-template").html()
max_score = _.max(member.score for member in most_active.members[0..9])
for mp in most_active.members[0..9]
    member = new Member mp
    dict = member.toJSON()
    dict.thumbnail_url = member.get_portrait_thumbnail(64)
    if dict.party
        url = URL_CONFIG['api_party'] + dict.party + '/logo/?dim=32x32'
        dict.party_thumbnail_url = url
    else
        dict.party_thumbnail_url = null

    # Better scaling here too
    dict.member_activity_percentage = mp.score / max_score * 100
    $ul.append $(template(dict))
