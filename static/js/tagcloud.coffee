(function($) {
    "use strict";

    $.widget("ui.tag_cloud", {
        options: {
            tags: null,
        },

        _create: function() {
            var container = $("<div class='tag_cloud_items'/>")
                .appendTo(this.element);

            var tag_list = $("<ul/>")
                .attr("class", "tag_list")
                .appendTo(container);

            var min_count;
            var max_count;
            var min_font_size;
            var max_font_size;
            var min_opacity;
            var weight_scale;
            var font_size_delta;
            var tags = this.options.tags;

            min_count = Infinity;
            max_count = 0;

            for (var i = 0; i < tags.length; i++) {
                var count = tags[i].count;

                if (count < min_count)
                    min_count = count;
                if (count > max_count)
                    max_count = count;
            }

            min_count = Math.log(min_count);
            max_count = Math.log(max_count);

            min_opacity = 0.6;
            min_font_size = 10;
            max_font_size = 20;
            font_size_delta = max_font_size - min_font_size;

            weight_scale = max_count - min_count;

            for (var i = 0; i < tags.length; i++) {
                var tag = tags[i];
                var weight;
                var font_size;
                var opacity;
                var li;

                weight = (Math.log(tag.count) - min_count);
                weight /= weight_scale;

                font_size = min_font_size;
                font_size += Math.round(font_size_delta * weight);

                li = $("<li/>");
                opacity = min_opacity + (1.0 - min_opacity) * weight;

                $("<a/>").
                    text(tag.name).
                    attr({
                            title:"" + tag.count,
                            href:tag.url,
                    }).
                    css("opacity", opacity).
                    appendTo(li);

                li.children().css("fontSize", font_size + "px");
                li.appendTo(tag_list);
            }
        }
    });
})(jQuery);
