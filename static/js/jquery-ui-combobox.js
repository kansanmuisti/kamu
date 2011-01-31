var SEARCH_DELAY                = 200;
var REMOTE_LOOKUP_TIMEOUT       = 5000;
var REMOTE_LOOKUP_MAX_RESULTS   = 500;

(function( $ ) {
    $.widget( "ui.combobox", {
        options: {
            source_url  : null,
            max_results : REMOTE_LOOKUP_MAX_RESULTS,
            any_text    : false,
            button      : true,
        },
        _create: function() {
            var self = this;
            var container = $("<span>")
                .addClass("combobox_container")
                .insertBefore(this.element);
            var last_val = null;
            var search_active = false;
            var search_callback = null;
            var sel_timer = null;

            if (typeof(String.prototype.trim) === "undefined") {
                String.prototype.trim = function() {
                    return String(this).replace(/^\s+|\s+$/g, '');
                };
            }

            function ajax_data(search_term) {
                data = {
                        max_results : self.options.max_results,
                        name        : search_term,
                };
                return data;
            }

            function ajax_result(data, autocomplete_callback) {
                last_val = data[0];
                autocomplete_callback(data);
            }

            function autocomplete_source(request, response) {
                search_active = true;
                self.xhr = $.ajax({
                    cache   : true,
                    url     : self.options.source_url,
                    dataType: "json",
                    timeout : REMOTE_LOOKUP_TIMEOUT,
                    data    : ajax_data(request.term.trim()),

                    success : function(data) {
                        ajax_result(data, response);
                    },
                    error   : function(xhr) {
                        if (xhr == self.xhr)
                            ajax_result([], response);
                    },
                    complete: function() {
                        search_active = false;
                        if (search_callback)
                            search_callback();
                        self.xhr = null;
                    },
                });
            }

            var input = $(this.element)
                .appendTo( container )
                .autocomplete({
                    minLength   : 1,
                    delay       : SEARCH_DELAY,

                    source      : autocomplete_source,
                    open        : function() {
                        $(this).removeClass("ui-corner-all").
                                        addClass("ui-corner-top");
                    },
                    close       : function() {
                        $(this).removeClass("ui-corner-top").
                                        addClass("ui-corner-all");
                    }
                })
                .addClass("ui-widget ui-widget-content ui-corner-left");

            input.bind("autocompleteselect", function(event, ui) {
                var val = input.val();
                last_val = ui.item.value;
                input.val(last_val);
                /*
                 * Don't trigger the event for keyboard selection. In
                 * that case we trigger it already through the keypress
                 * handler and this would only cause a double trigger.
                 */
                if (event.button >= 0)
                    self._trigger("selected", null, { value: val });
            });

            function setup_async_comp(callback) {
                search_callback = callback;
                sel_timer = setTimeout(callback, SEARCH_DELAY + 50);
            }

            function reset_async_comp() {
                search_callback = null;
                if (sel_timer) {
                    clearTimeout(sel_timer);
                    sel_timer = null;
                }
            }

            function next_tab(elem) {
                var r;
                while (true) {
                    r = elem.nextAll(":tabbable").first();
                    if (r.length)
                        return r;
                    r = elem.parent();
                    if (!r.length)
                        return null;
                    elem = r;
                }
            }

            function stricmp(str1, str2) {
                s1 = "";
                s2 = "";
                if (str1)
                    s1 = str1.toLocaleLowerCase();
                if (str2)
                    s2 = str2.toLocaleLowerCase();
                if (s1 < s2)
                    return -1;
                if (s1 > s2)
                    return 1;
                return 0;
            }

            function trigger_selected(force_leave, async) {
                var val = input.val().trim();

                if (stricmp(last_val, val) && search_active) {
                    setup_async_comp(function() {
                            trigger_selected(force_leave, true);
                    });
                    return;
                }

                if (!stricmp(last_val, val)) {
                    input.val(last_val);
                    self._trigger("selected", null, { value: last_val });
                }
                if (force_leave) {
                    if (stricmp(last_val, val))
                        input.val("");
                    if (async) {
                        input.autocomplete("close");
                        r = next_tab(input);
                        if (r)
                            r.focus();
                    }
                } else {
                    input.autocomplete("option", "disabled", true);
                    input.autocomplete("close");
                }
                reset_async_comp();
            }

            function check_valid(event, force_leave) {
                var val = input.val().trim();

                if (val == "") {
                    if (!force_leave)
                        event.preventDefault();
                    return;
                }
                if (self.options.any_text || !stricmp(last_val, val)) {
                    trigger_selected(force_leave, false);
                } else {
                    setup_async_comp(function() {
                        trigger_selected(force_leave, true);
                    });
                    event.preventDefault();
                }
            }

            input.bind("keypress", function(e) {
                var keyCode = $.ui.keyCode;
                switch (e.keyCode) {
                case keyCode.ENTER:
                case keyCode.NUMPAD_ENTER:
                    check_valid(e, false);
                    break;
                case keyCode.TAB:
                    check_valid(e, true);
                    break;
                default:
                    reset_async_comp();
                    input.autocomplete("option", "disabled", false);
                }
            });

            function button_click() {
                /* close if already visible */
                if ( input.autocomplete( "widget" ).is( ":visible" ) ) {
                    input.autocomplete("option", "minLength", 1);
                    input.autocomplete( "close" );
                    return;
                }

                input.autocomplete("option", "minLength", 0);
                /*
                 * pass empty string as value to search for,
                 * displaying all results
                 */
                input.autocomplete( "search", "" );
                input.focus();
            };

            function add_button() {
                $("<button type='button'>&nbsp;</button>")
                    .attr("tabIndex", -1)
                    .insertAfter(input)
                    .button({
                        icons: {
                            primary: "ui-icon-triangle-1-s"
                        },
                        text: false,
                    })
                    .removeAttr( "title" )
                    .removeClass( "ui-corner-all" )
                    .addClass( "ui-corner-right ui-button-icon" )
                    .click(button_click);
            }

            if (self.options.button)
                add_button();
	    }
	});
})( jQuery );
