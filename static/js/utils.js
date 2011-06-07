"use strict";

(function ($) {
// VERTICALLY ALIGN FUNCTION
$.fn.vAlign = function() {
	return this.each(function(i){
		var ah = $(this).height();
		var ph = $(this).parent().height();
		var mh = Math.ceil((ph-ah) / 2);
		$(this).css('margin-top', mh);
	});
};

$.fn.color_gradient = function(pos, options) {
    var settings = {
        'colors':     [[255, 0, 0], [0, 255, 0], [0, 0, 255]],
        'anchors':    [0, 50, 100],
        'color-property': 'color',
    }
    if (options)
        $.extend(settings, options);

    var anchors = settings['anchors'];
    var colors = settings['colors'];
    var i;
    for (i = 0; i < anchors.length; i++)
        if (pos <= anchors[i])
            break;
    if (!i && pos < anchors[0]) {
        pos = anchors[0];
    } else if (i == anchors.length && pos > anchors[anchors.length - 1]) {
        i = anchors.length - 1;
        pos = anchors[i];
    }

    low_anchor = anchors[i ? i - 1 : 0];
    low_color = colors[i ? i - 1 : 0];
    high_anchor = anchors[i];
    high_color = colors[i];

    if (!(high_anchor - low_anchor))
        ratio = 0;
    else
        ratio = (pos - low_anchor) / (high_anchor - low_anchor);

    var color_str = "#";
    for (i = 0; i < 3; i++) {
        var num = low_color[i] + (high_color[i] - low_color[i]) * ratio;
        num = Math.floor(num);
        var num_str = num.toString(16);
        if (num_str.length == 1)
            num_str = "0" + num_str;
        color_str += num_str;
    }

    return this.each(function() {
        $(this).css(settings["color-property"], color_str);
    });
}
})(jQuery);

function emphasize_matching_parts(query, text) {
    var trailing_space = query[query.length - 1] == " ";
    var words = query.ltrim().split(/ +/);
    var cnt = words.length;
    var i;

    if (trailing_space)
        cnt--;
    for (var i = 0; i < cnt; i++) {
        var pat = "( |^)(" + words[i] + ")";

        if (i < cnt - 1 || trailing_space)
            pat += "( |$)";
        else
            pat += "(.|$)";
        var old_text = text;
        var text = text.replace(new RegExp(pat, "ig"),
                            "$1<b>$2</b>$3");
        if (old_text == text)
            return null;
    }

    return text;
}

