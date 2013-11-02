class @ActivityScoresView extends Backbone.View
    initialize: (options) ->
        @scores = options.scores
        @render()

    render: ->
        score_list = @scores.models
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

        $.plot $(@el), [ act_histogram ],
            series:
                bars:
                    show: true
                    barWidth: 120 * 24 * 60 * 60 * 1000     # milliseconds
                    align: "center"
            xaxis:
                mode: "time"
    
        return @
