class @ActivityScoresView extends Backbone.View
    initialize: (options) ->
        @scores = options.scores
        @render()

    render: ->
        scrs = @scores.models
        act_keys = (t[0] for t in activity_types)
        act_names = (t[1] for t in activity_types)
        act_histograms = {}

        for key in act_keys
            act_histograms[key] = {x: [], y: [], key: key}

        data_idx = 0
        bin_idx = 0
        ts = new Date(scrs[0].attributes.time)
        while data_idx < scrs.length
            act = scrs[data_idx].attributes
            this_date = new Date(act.time)
            while (ts < this_date)
                for key of act_histograms
                    act_histograms[key].x.push new Date(ts)
                    act_histograms[key].y.push 0
                bin_idx += 1
                ts.setDate(ts.getDate() + 1)

            for key of act_histograms
                act_histograms[key].x.push this_date
                act_histograms[key].y.push 0
            act_histograms[String(act.type)].y[bin_idx] += act.score

            data_idx += 1
            bin_idx += 1
            ts.setDate(ts.getDate() + 1)

        hist_list = (v for k, v of act_histograms)

        graph = new MultiresStackedGraph @el, hist_list

        return @
