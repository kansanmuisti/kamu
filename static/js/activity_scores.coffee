class @ActivityScoresView extends Backbone.View
    initialize: (collection, options) ->
        @el = options.el
        end_date = options.end_date
        activity_daily_avg = options.activity_daily_avg

        collection.bind 'reset', @add_all_items

        time = new Date(end_date)
        year = time.getFullYear()
        month = time.getMonth()
        start_time = new Date(year - 2, month + 1, 1)
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

        @plot_series = []
        @plot_global_options = @get_plot_global_options(start_time, end_time)

        $(window).resize =>
            @draw_plot()

        resolution = 'month'
        if activity_daily_avg
            @avg_bin_score = activity_daily_avg * 30
        else
            @avg_bin_score = null

        params =
            resolution: resolution
            since: start_time_str
            until: end_time_str
            limit: 0
        collection.fetch
            reset: true
            data: params

    draw_plot: ->
        if @plot_series.length == 0
            return

        $.plot $(@el), @plot_series, @plot_global_options

    get_histogram: (score_list) ->
        if score_list.length == 0
            return []

        act_histogram = []
        if @avg_bin_score
            max_score = @avg_bin_score + 20
        else
            max_score = 0

        data_idx = 0
        while data_idx < score_list.length
            act = score_list[data_idx].attributes
            time = act.time
            score = act.score

            while data_idx + 1 < score_list.length
                act = score_list[data_idx + 1].attributes

                if act.time != time
                    break

                score += act.score
                data_idx += 1

            time = new Date(time).getTime()
            column = [ time, score ]
            act_histogram.push column

            max_score = Math.max max_score, score

            data_idx += 1

        return [act_histogram, max_score]

    render: ->
        [act_histogram, max_score] = @get_histogram(@scores.models)

        if act_histogram.length == 0
            return @

        if @avg_bin_score
            markings = [
                yaxis:
                    from: @avg_bin_score
                    to: @avg_bin_score
            ]
        else
            markings = []

        @plot_global_options['yaxis']['max'] = max_score
        @plot_global_options['grid']['markings'] = markings

        @plot_series.push
            data: act_histogram
            color: "#00c0c0"
            bars:
                show: true
                fill: 1
                barWidth: 16 * 24 * 60 * 60 * 1000     # milliseconds
                align: "center"

        @draw_plot()

        return @

    get_plot_global_options: (start_time, end_time) ->
        return {
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
                min: start_time.getTime() - 20 * 24 * 60 * 60 * 1000
                max: end_time.getTime()

            yaxis:
                show: false

            grid:
                borderWidth:
                    top: 0
                    bottom: 1
                    left: 0
                    right: 0
        }

    add_all_items: (collection) =>
        @scores = collection
        @render()

