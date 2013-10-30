class @ActivityScoresView extends Backbone.View
    initialize: ->
        @render()

    render: ->
        date = new Date(activity_counts[0].activity_date)
        end_date = new Date(activity_counts[activity_counts.length-1].activity_date)

        act_keys = (t[0] for t in activity_types)
        act_names = (t[1] for t in activity_types)
        act_histograms = {}

        for key in act_keys
            act_histograms[key] = {x: [], y: [], key: key}

        data_idx = 0
        bin_idx = 0
        while date <= end_date
            ts = date.getTime()
            for key of act_histograms
                act_histograms[key].x.push new Date(ts)
                act_histograms[key].y.push 0
            while data_idx < activity_counts.length
                act = activity_counts[data_idx]
                if new Date(act.activity_date) > date
                    break
                score = act.count*activity_weights[act.type]
                act_histograms[act.type].y[bin_idx] += score
                data_idx += 1
            date.setDate(date.getDate()+1)
            bin_idx += 1

        hist_list = (v for k, v of act_histograms)

        graph = new MultiresStackedGraph @el, hist_list

        return @
