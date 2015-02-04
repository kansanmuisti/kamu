class @ActivityScoresView extends Backbone.View
    initialize: (@collection, options) ->
        @options = _.extend {}, options
        @el = options.el

        @collection.bind 'reset', =>
            @scores_fetched.resolve()

        if @options.show_average_activity
            @avg_act_collection = new ParliamentActivityScoresList
            @avg_act_collection.bind 'reset', =>
                @avg_scores_fetched.resolve()

        @user_filters = {}
        @type_filter = null

        @reset()

    filter_keyword: (kw) ->
        if kw
            @user_filters['keyword'] = kw
        else
            delete @user_filters['keyword']
        @reset()

    filter_type: (types) ->
        if not types
            @type_filter = []
        else
            @type_filter = types
        @render()

    reset: ->
        time = new Date(@options.end_date)
        year = time.getFullYear()
        month = time.getMonth()
        start_time = new Date(year - 4, month + 1, 1)
        start_time_str = start_time.getFullYear() + "-" +  \
                          (start_time.getMonth() + 1) + "-" + \
                          start_time.getDate()

        time =  new Date(new Date(year, month + 1, 1).getTime() - 1)
        year = time.getFullYear()
        month = time.getMonth()
        day = time.getDate()
        end_time = new Date(year, month, day)
        end_time_str = end_time.getFullYear() + "-" + \
                       (end_time.getMonth() + 1) + "-" + \
                       end_time.getDate()

        @plot_global_options = @get_plot_global_options(start_time, end_time)

        resolution = 'month'

        @scores_fetched = $.Deferred()
        @avg_scores_fetched = $.Deferred()

        params = _.extend {}, @user_filters,
            resolution: resolution
            since: start_time_str
            until: end_time_str
            limit: 0

        @collection.fetch
            reset: true
            data: params

        if @avg_act_collection
            params['calculate_average'] = true
            @avg_act_collection.fetch
                reset: true
                data: params
        else
            @avg_scores_fetched.resolve()

        $.when(@scores_fetched, @avg_scores_fetched).done =>
            $(window).resize =>
                @draw_plot()
            @render()

    draw_plot: ->
        if @plot_series.length == 0
            return

        $.plot $(@el), @plot_series, @plot_global_options

    get_histogram: (score_list) ->
        if score_list.length == 0
            return []

        act_histogram = []

        max_score = 0
        data_idx = 0
        while data_idx < score_list.length
            act = score_list[data_idx].attributes
            time = act.time
            score = act.score
            if @type_filter and @type_filter.length
                if act.type not in @type_filter
                    data_idx += 1
                    continue

            while data_idx + 1 < score_list.length
                act = score_list[data_idx + 1].attributes

                if @type_filter and @type_filter.length
                    if act.type not in @type_filter
                        break

                if act.time != time
                    break

                score += act.score
                data_idx += 1

            time = new Date(time).getTime()
            column = [time, score]
            act_histogram.push column

            max_score = Math.max max_score, score

            data_idx += 1

        return [act_histogram, max_score]

    render: ->
        [act_histogram, max_score] = @get_histogram @collection.models
        if act_histogram.length == 0
            return @

        if @avg_act_collection
            [avg_histogram, avg_max_score] = @get_histogram @avg_act_collection.models
            max_score = Math.max max_score, avg_max_score
            draw_avg = avg_histogram.length != 0
        else
            draw_avg = false

        @plot_global_options['yaxis']['max'] = max_score
        @plot_global_options['series'] =
            curvedLines:
                active: draw_avg
                monotonicFit: true

        @plot_series = []
        @plot_series.push
            data: act_histogram
            color: "#00c0c0"
            bars:
                show: true
                fill: 1
                barWidth: 16 * 24 * 60 * 60 * 1000     # milliseconds
                align: "center"

        if draw_avg
            @plot_series.push
                data: avg_histogram
                color: "rgba(255, 255, 255, 0.6)"
                shadowSize: 0
                lines:
                    show: true
                curvedLines:
                    apply: true

        @draw_plot()

        return @

    get_plot_global_options: (start_time, end_time) ->
        x_start = end_time.getTime() - (2 * 365 + 20) * 24 * 60 * 60 * 1000
        if x_start < start_time.getTime()
            x_start = start_time.getTime()
        return {
            pan:
                interactive: true
            xaxis:
                mode: "time"
                tickLength: 5
                tickFormatter: (val, axis) ->
                    d = new Date(val)

                    if d.getMonth() == 0
                        format_str = "MMM<br>YYYY"
                    else
                        format_str = "MMM"
                    return moment(d).format(format_str)
                min: x_start
                max: end_time.getTime()
                panRange: [start_time.getTime() - 20 * 24 * 60 * 60 * 1000, end_time.getTime()]

            yaxis:
                show: false
                panRange: false
                min: 0

            grid:
                borderWidth:
                    top: 0
                    bottom: 1
                    left: 0
                    right: 0
        }
