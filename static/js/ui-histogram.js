(function($) {
    "use strict";
    $.widget("ui.histogram", {
        options: {
            data: [ [ "data11", "data12", ], [ "data21", "data22*", "data23", ], ],
            gap: 3,
            normal_color: "black",
            selected_color: "green",
            hover_color: "#444",
            tooltip_options: {},
            tooltip_handler: null,
            click_handler: null,
        },
        _create: function() {
             var width = this.element[0].offsetWidth;
             var height = this.element[0].offsetHeight;
             var canvas = Raphael(this.element[0], width, height);

             $(this).data("canvas", canvas);
             $(this).data("width", width);
             $(this).data("height", height);
        },
        update: function(data, low_percent, high_percent,
                         selected_bin, selected_item) {
             var width = $(this).data("width");
             var height = $(this).data("height");
             var canvas = $(this).data("canvas");
             var normal_color = this.options.normal_color;
             var gap = this.options.gap;

             var max_cnt = 0;
             for (var i = 0; i < data.length; i++) {
                 var cnt = data[i].length;

                 if (cnt > max_cnt) {
                    max_cnt = cnt;
                }
             }

             if (!max_cnt) {
                 console.log("ui-histogram: invalid data option");
                 return;
             }

             var step_x = width / data.length;
             var x_axis_height = 30;
             var step_y = (height - x_axis_height) / max_cnt;

             if (step_y > step_x)
                 step_y = step_x;

             var rec_width = step_x - gap;
             var rec_height = step_y - gap;
             var half_gap = gap / 2;
             var normal_color = this.options.normal_color;
             var hover_color = this.options.hover_color;
             var pos_x;
             var pos_y;
             var tooltip_options = this.options.tooltip_options;
             var tooltip_handler = this.options.tooltip_handler;
             var click_handler = this.options.click_handler;

             function draw_rect(x, y, w, h, color, tooltip_ptr)
             {
                 var rect = canvas.rect(x, y, w, h);

                 rect.attr("fill", color);
                 rect.attr("stroke", color);
                 $(rect.node).addClass("histogram_box");
                 if (tooltip_handler) {
                     var options =  {
                         delay: 200,
                         fade: 200,
                         bodyHandler: function() {
                             return tooltip_handler(tooltip_ptr);
                         },
                     };
                     $.extend(options, tooltip_options);
                     $(rect.node).tooltip(options);
                 }
                 if (click_handler)
                     $(rect.node).click(function(event) {
                         click_handler(event, tooltip_ptr);
                     });

                 rect.hover(
                     function (e) {
                         if (this.selected_frame)
                             return;
                         this.attr({
                             fill:hover_color,
                             stroke:hover_color,
                         });
                     },
                     function (e) {
                         var color = normal_color;

                         if (this.selected)
                             color = selected_color;
                         this.attr({
                             fill:color,
                             stroke:color,
                         });
                     });

                 return rect;
             }

             function draw_line(x1, y1, x2, y2)
             {
                 var path = canvas.path("M" + x1 + " " + y1 +
                                        "L" + x2 + " " + y2);

                 path.attr("stroke", normal_color);

                 return path;
             }

             function _draw_text(canv, x, y, text, anchor)
             {
                 var text_elem = canv.text(x, y, text);

                 text_elem.attr("text-anchor", anchor);
                 text_elem.attr("fill", normal_color);
                 text_elem.attr("font-size", 15);
                 text_elem.attr("font-family", "verdana");

                 return text_elem;
             }

             function get_text_sizes(text)
             {
                var dummy_canvas = Raphael(0, 0, 100, 100);

                var text_elem = _draw_text(dummy_canvas, 0, 0, text);

                var bbox = text_elem.getBBox();
                var sizes = [bbox.width, bbox.height];

                text_elem.remove();
                dummy_canvas.remove();

                return sizes;
             }

             function draw_text(x, y, text, anchor)
             {
                 var sizes = get_text_sizes(text);

                 return _draw_text(canvas, x, y + sizes[1] / 2, text, anchor);
             }

             function draw_triangle(x, y)
             {
                 var len = step_x;
                 var height = Math.sqrt(3/4) * len;

                 var pstr = "M " + x + " " + (y + height);

                 pstr += " l " + (len / 2) + " " + (-height);
                 pstr += " l " + (len / 2) + " " + height;
                 pstr += " z";

                 var path = canvas.path(pstr);
                 path.attr("fill", normal_color)
                 path.attr("stroke", normal_color);

                 return path;
             }

             canvas.clear();

             pos_y = height - x_axis_height + 2 * gap;
             draw_line(0, pos_y, width, pos_y);
             pos_x = selected_bin * step_x;
             draw_triangle(pos_x, pos_y - 5);

             pos_y += 2 * gap;

             var low_text = draw_text(0, pos_y,
                                    Math.round(low_percent) + " %", "start");
             var high_text = draw_text(width, pos_y,
                                    Math.round(high_percent) + " %", "end");

             function overlap(x1, w1, x2, w2)
             {
                 return (x1 > x2 && x1 < x2 + w2) ||
                        (x2 > x1 && x2 < x1 + w1);
             }

             var low_bbox = low_text.getBBox();
             var high_bbox = high_text.getBBox();

             var bin_val = low_percent;

             bin_val += (high_percent - low_percent) / data.length *
                 selected_bin;
             bin_val = Math.round(bin_val);
             var text_sizes = get_text_sizes(bin_val + " %");

             pos_x = pos_x + step_x / 2 - text_sizes[0] / 2;

             if (selected_bin != -1 &&
                 !overlap(pos_x, text_sizes[0], low_bbox.x, low_bbox.width) &&
                 !overlap(pos_x, text_sizes[0], high_bbox.x, high_bbox.width))
                 draw_text(pos_x, pos_y, bin_val + " %", "start");

             for (var i = 0; i < data.length; i++) {
                 var d = data[i];

                 pos_x = step_x * i;
                 pos_y = height - x_axis_height;
                 for (var j = 0; j < d.length; j ++) {
                     var selected = false;

                     var rect = draw_rect(pos_x + half_gap,
                               pos_y - step_y + half_gap,
                               rec_width, rec_height, normal_color, d[j]);

                     if (i == selected_bin && j == selected_item) {
                         var selected_color = this.options.selected_color;

                         rect.selected_frame = true;
                         rect = draw_rect(pos_x + half_gap * 2,
                                   pos_y - step_y + half_gap * 2,
                                   rec_width - half_gap * 2,
                                   rec_height - half_gap * 2,
                                   selected_color, d[j]);
                         rect.selected = true;
                     }

                     pos_y -= step_y;
                 }
             }

        }
    });
})(jQuery);
