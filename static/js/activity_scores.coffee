class @ActivityScoresView extends Backbone.View
    initialize: (options) ->
        @scores = options.scores
        @start_time = options.start_time
        @end_time = options.end_time
        @render()

    render: ->
        score_list = @scores.models

        if score_list.length == 0
            return @

        act_histogram = []

        data_idx = 0
        while data_idx < score_list.length
            act = score_list[data_idx].attributes
            time = act.time
            score = act.score

            while data_idx + 1 < score_list.length
                data_idx += 1

                act = score_list[data_idx].attributes

                if act.time != time
                    break

                score += act.score

            time = new Date(time).getTime()
            column = [ time, score ]
            act_histogram.push column

            data_idx += 1

        colors = ["#00c0c0"]
        $.plot $(@el), [ act_histogram ],
            colors: colors
            series:
                bars:
                    show: true
                    fill: 1
                    barWidth: 16 * 24 * 60 * 60 * 1000     # milliseconds
                    align: "center"
            xaxis:
                mode: "time"
                tickLength: 5
                min: @start_time.getTime() - 20 * 24 * 60 * 60 * 1000
                max: @end_time.getTime()

            yaxis:
                show: false

            grid:
                borderWidth:
                    top: 0
                    bottom: 1
                    left: 0
                    right: 0
    
        return @
