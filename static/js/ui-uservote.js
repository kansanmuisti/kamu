(function($) {
    $.widget("ui.user_vote_panel", {
        options: {
            init_state      : "clear",
            toggle_url      : null,
            disabled        : false,
            disabled_text   : "Voting disabled",
            up_count        : 0,
            down_count      : 0,
        },

        _toggle_vote: function(self, is_up, e) {
            function update_button_class(is_up, state) {
                var up_down = is_up ? "up" : "down";
                var yes_no = is_up ? "yes" : "no";
                var button = $('.user_vote_' + up_down + ' .user_vote_button');

                if (state == up_down) {
                    button.removeClass(yes_no + '_vote');
                    button.addClass(yes_no + '_vote_selected');
                } else {
                    button.removeClass(yes_no + '_vote_selected');
                    button.addClass(yes_no + '_vote');
                }
            }

            function update_counter(is_up, value) {
                var up_down = is_up ? "up" : "down";
                var counter = $('.user_vote_' + up_down + ' .user_vote_count');

                counter.text(value);
            }

            var success_func = function(resp) {
                update_counter(true, resp.up);
                update_counter(false, resp.down);
                update_button_class(true, resp.selected);
                update_button_class(false, resp.selected);
            };

            var up_down = is_up ? "up" : "down";
            $.ajax({
                type: "POST",
                data: "vote=" + up_down,
                dataType: "json",
                url:self.options.toggle_url,
                success: success_func,
            });

            return false;
        },

        _create_vote: function(self, container, is_up)
        {
            var up_down = is_up ? "up" : "down";
            var yes_no = is_up ? "yes" : "no";
            var count = is_up ? self.options.up_count : self.options.down_count;

            var vote = $("<span>")
                .addClass("user_vote_" + up_down)
                .appendTo(container);

            var vote_button = $("<a>")
                .attr("href", "#")
                .css("float", "left")
                .addClass("user_vote_button")
                .appendTo(vote);

            var bclass;

            if (self.options.init_state == up_down)
                bclass = yes_no + "_vote_selected";
            else
                bclass = yes_no + "_vote";

            vote_button.addClass(bclass);

            var vote_count = $("<p>" + count + "</p>")
                .addClass("user_vote_count")
                .appendTo(vote);

            vote_button.click(function(e) {
                    if (self.options.disabled) {
                        alert(self.options.disabled_text);
                        return false;
                    }
                    return self._toggle_vote(self, is_up, e);
            });

            return vote;
        },
        _create: function() {
            var self = this;
            var container = $("<span>")
                .css({
                    "margin-right":"16px",
                    "float":"left",
                    })
                .addClass("user_vote")
                .appendTo(this.element);


            this._create_vote(self, container, true);
            this._create_vote(self, container, false);
        }
    });
})(jQuery);
