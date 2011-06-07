(function($) {
    "use strict";
    $.widget("ui.percentagebar", {
        options: {
            "gradient_options":null,
            "color":"black",
            "height":"5px",
            "value":50,
        },
        _get_bar: function() {
            return $(this).data("bar");
        },
        _get_value: function() {
            return $(this).data("value");
        },
        _set_color: function() {
            var bar = this._get_bar();
            var color = this.options.color;

            if (color == "gradient") {
                var gradient_opts = {
                    "color_property": "background-color",
                };
                $.extend(gradient_opts, this.options.gradient_opts);
                var value = this._get_value();
                bar.color_gradient(value, gradient_opts);
            } else {
                bar.css("background-color", this.options.color);
            }
        },
        _set_value: function(value) {
            $(this).data("value", value);
            var bar = this._get_bar()
            bar.css("width", value + "%");
            this._set_color();
        },
        _create: function() {
            var bar = $("<div>").
                css({
                    "height":this.options.height,
                    }).
                appendTo(this.element);
            $(this).data("bar", bar);
            this._set_value(this.options.value);

        },
        set_value: function(value) {
            this._set_value(value);
        }
    });
})(jQuery);
