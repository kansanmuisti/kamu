var SEARCH_DELAY                = 200;
var REMOTE_LOOKUP_TIMEOUT       = 5000;
var REMOTE_LOOKUP_MAX_RESULTS   = 500;
var THUMBNAIL_DEFAULT_WIDTH     = 40;
var THUMBNAIL_DEFAULT_HEIGHT    = 40;

var THUMBNAIL_BLOCK_CLASS       = "combobox_thumbnail_block";

(function( $ ) {
    $.widget( "ui.combobox", {
        options: {
            source_url  : null,
            max_results : REMOTE_LOOKUP_MAX_RESULTS,
            any_text    : false,
            button      : true,
            thumbnail   : false,
        },
        _create: function() {
            var self = this;
            var container = $("<span>")
                .addClass("combobox_container")
                .insertBefore(this.element);
            var last_item = null;
            var search_active = false;
            var search_callback = null;
            var sel_timer = null;
            var thumbnail_width;
            var thumbnail_height;
            var input;

            if (typeof(String.prototype.ltrim) === "undefined") {
                String.prototype.ltrim = function() {
                    var s = String(this);
                    var len = s.length;
                    var l = 0;

                    while(l < len && s[l] == ' ')
                        l++;
                    return s.substring(l, len);
                };
            }

            if (self.options.thumbnail) {
                /* dummy element to get access to a class's css properties */
                var dummy = $('<div>').addClass(THUMBNAIL_BLOCK_CLASS).
                                      appendTo(document.body);

                /*
                 * parseInt also strips the trailing px and convert auto
                 * to Nan.
                 */
                thumbnail_width = parseInt(dummy.css('width'));
                thumbnail_height = parseInt(dummy.css('height'));

                dummy.remove();
                if (isNaN(thumbnail_width) || isNaN(thumbnail_height)) {
                    thumbnail_width = THUMBNAIL_DEFAULT_WIDTH;
                    thumbnail_height = THUMBNAIL_DEFAULT_HEIGHT;
                }
            }

            function ajax_data(search_term) {
                data = {
                        max_results : self.options.max_results,
                        name        : search_term,
                };
                if (self.options.thumbnail) {
                    $.extend(data, {
                        thumbnail_width     : thumbnail_width,
                        thumbnail_height    : thumbnail_height,
                    });
                }
                return data;
            }

            function normalize_ajax_result(data) {
                if (!data)
                    return {}
                return {
                    label       : data[0],
                    value       : data[0],
                    thumbnail   : data[1],
                    url         : data[2],
                };
            }

            function ajax_result(data, autocomplete_callback) {
                last_item = normalize_ajax_result(data[0]);
                autocomplete_callback(data);
            }

            function autocomplete_source(request, response) {
                search_active = true;
                self.xhr = $.ajax({
                    cache   : true,
                    url     : self.options.source_url,
                    dataType: "json",
                    timeout : REMOTE_LOOKUP_TIMEOUT,
                    data    : ajax_data(request.term.ltrim()),

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

            input = $(this.element)
                .appendTo( container )
                .autocomplete({
                    minLength   : 1,
                    delay       : SEARCH_DELAY,
                    appendTo    : container,

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

            function autocomplete_normalize(items) {
                var norm_items = [];
                $.map(items, function(item) {
                    norm_items.push(normalize_ajax_result(item));
                });
                return norm_items;
            }

            function autocomplete_renderitem_plain(ul, item) {
                var list_item = "<a>" +
                                emphasize_matching_parts(input.val(),
                                                        item.value) +
                                "</a>";
                var elem = $("<li>").data("item.autocomplete", item)
                        .append(list_item)
                        .appendTo(ul);

                return elem;
            }

            function autocomplete_renderitem(ul, item) {
                var list_item =
                    "<a class='combobox_list_item'>"                    +
                        "<span class='" + THUMBNAIL_BLOCK_CLASS + "'>";

                if (item.thumbnail[0])
                    list_item += "<img src='" + item.thumbnail + "'/>";

                list_item +=
                        "</span>"                                       +
                        "<p class='combobox_text_block'>"               +
                            emphasize_matching_parts(input.val(),
                                                    item.value)         +
                        "</p>"                                          +
                    "</a>";

                var elem = $("<li>").data("item.autocomplete", item)
                        .append(list_item)
                        .appendTo(ul);
                return elem;
            };

            input.data("autocomplete")._normalize = autocomplete_normalize;
            if (self.options.thumbnail) {
                input.data("autocomplete")._renderItem =
                                            autocomplete_renderitem;
            } else {
                input.data("autocomplete")._renderItem =
                                            autocomplete_renderitem_plain;
            }

            input.bind("autocompleteselect", function(event, ui) {
                var val = input.val();
                last_item = ui.item;
                input.val(last_item.value);
                /*
                 * Don't trigger the event for keyboard selection. In
                 * that case we trigger it already through the keypress
                 * handler and this would only cause a double trigger.
                 */
                if (event.button >= 0)
                    self._trigger("selected", null, last_item);
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
                var val = input.val().ltrim();

                if (stricmp(last_item.value, val) && search_active) {
                    setup_async_comp(function() {
                            trigger_selected(force_leave, true);
                    });
                    return;
                }

                if (!stricmp(last_item.value, val)) {
                    input.val(last_item.value);
                    self._trigger("selected", null, last_item);
                }
                if (force_leave) {
                    if (stricmp(last_item.value, val))
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
                var val = input.val().ltrim();

                if (val == "") {
                    if (!force_leave)
                        event.preventDefault();
                    return;
                }
                if (self.options.any_text || !stricmp(last_item.value, val)) {
                    trigger_selected(force_leave, false);
                } else {
                    setup_async_comp(function() {
                        trigger_selected(force_leave, true);
                    });
                    event.preventDefault();
                }
            }

            input.bind("keydown", function(e) {
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
