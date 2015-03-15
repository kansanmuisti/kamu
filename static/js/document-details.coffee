doc = new Document document_json

SEMSI_BASE = "http://semsi.kansanmuisti.fi:8080/"

doc_list_el = $(".similar-documents ol")
$(".proposal-summary").expander
    slicePoint: 1000
    hasBlocks: true

template = _.template $.trim $("#similar-document-item-template").html()

$.ajax
    type: "GET"
    dataType: "json"
    url: SEMSI_BASE + 'index/kamu/similar'
    contentType: "application/json; charset=utf-8"
    data:
        id: doc.get 'url_name'
    success: (data, status) ->
        count = 0
        for d in data
            if d.relevance < 0.5
                continue
            if d.id == doc.get 'url_name'
                continue
            d.url = URL_CONFIG['document_details'].replace 'DOC', d.id
            $el = $(template d)
            doc_list_el.append $el
            count++
            if count == 5
                break
        if count
            $(".similar-documents").removeClass 'hide'
