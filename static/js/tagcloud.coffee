(($) ->
    $.fn.tag_cloud = (tags) ->
        tag_list = $("<ul/>").attr("class", "items")

        min_count = Infinity
        max_count = 0
        for tag in tags
            count = tag.count
            if count < min_count
                min_count = count
            if count > max_count
                max_count = count

        min_count = Math.log(min_count)
        max_count = Math.log(max_count)
        min_opacity = 0.9
        min_font_size = 10
        max_font_size = 28
        font_size_delta = max_font_size - min_font_size
        weight_scale = max_count - min_count

        for tag in tags
            weight = (Math.log(tag.count) - min_count)
            weight /= weight_scale
            font_size = min_font_size
            font_size += Math.round(font_size_delta * weight)
            $li = $("<li/>")
            opacity = min_opacity + (1.0 - min_opacity) * weight
            $("<a/>").text(tag.name).attr(
                title: "" + tag.count
                href: tag.url
            ).css("opacity", opacity).appendTo $li
            $li.children().css "fontSize", font_size + "px"
            $li.appendTo tag_list

        this.append tag_list
) jQuery
