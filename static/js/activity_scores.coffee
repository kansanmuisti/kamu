

SECS_IN_MONTH = 86400 * 27
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
        @highlight_range = {}
        
        $el = $ @el

        MonthlyBar = Rickshaw.Class.create Rickshaw.Graph.Renderer.Bar,
            name: "monthbarhack"

            barWidth: (series) ->
                origin = series.stack[0]
                if not origin?
                    return 0
                @graph.x origin.x + SECS_IN_MONTH * (1-@gapSize)

            domain: ($super) ->
                domain = $super()
                domain.x = [domain.x[0], domain.x[1] + SECS_IN_MONTH]
                return domain

            _frequentInterval: ->
                magnitude: 0, count: 0
        
        @member_series =
            color: "#00c0c0"
            name: "Activity"
            data: []
            renderer: "monthbarhack"

        @avg_series =
            color: "#6f59bc"
            name: "Average activity"
            data: []
            renderer: "line"

            
        
        Rickshaw.Graph.Renderer.monthbar = MonthlyBar
        @graph = new Rickshaw.Graph
            width: $el.width()
            height: $el.height()
            element: $el[0]
            renderer: "multi"
            series: [@member_series, @avg_series]
        $(window).resize =>
            # Come on! Do scalable by default
            # people!
            @graph.configure
                width: $el.width()
                height: $el.height()
            @graph.update()
        @member_series.renderer.graph = @graph
        
        xaxis = new Rickshaw.Graph.Axis.Time graph: @graph
        @graph.render()
        xaxis.render()
        
        $(@graph.vis[0][0]).click (ev) =>
            x = @graph.x.invert ev.offsetX
            if x > @highlight_range.from and x < @highlight_range.to
                @el.trigger "plotdaterange", undefined
                return
            # Round to nearest month. For some
            # reason won't work with moment.js
            from = new Date x*1000
            from.setDate 1
            to = new Date from.getFullYear(), from.getMonth()+1, 0

            @el.trigger "plotdaterange",
                from: moment(from).format "YYYY-MM-DD"
                to: moment(to).format "YYYY-MM-DD"
        
        @graph.onUpdate =>
            # Hopefully everything is removed already
            el = $ @graph.vis[0][0]
            {from, to} = @highlight_range
            return if not from? and not to?
            [min, max] = @graph.dataDomain()
            from = from ? min
            to = to ? max
            
            @graph.vis.selectAll 'g'
            .attr "mask", "url(#selmask)"
            
            defs = @graph.vis.insert "defs", ":first-child"
            mask = defs.append "mask"
            .attr 'id', 'selmask'
            
            mask.append "rect"
            .attr 'x', 0
            .attr 'y', 0
            .attr 'width', "100%"
            .attr 'height', "100%"
            .attr 'fill', "#222"

            mask.append "rect"
            .attr 'x', @graph.x from
            .attr 'width', @graph.x(to) - @graph.x(from)
            .attr 'y', 0
            .attr 'height', '100%'
            .attr 'fill', 'white'
            
            @graph.vis.append("g").append "rect"
            .attr 'x', @graph.x from
            .attr 'width', @graph.x(to) - @graph.x(from)
            .attr 'y', "100%"
            .attr 'height', 2
            .attr 'stroke', 'black'
            .attr 'stroke-opacity', 0.5
            .attr 'stroke-width', 6
            .attr 'fill', 'none'
        

    

        #@reset()
    
    filter: ({keyword, type, date}={}) ->
        # TODO! Backbone doesn't seem to cancel
        # pending resets, which may cause client side
        # filters not to be applied if two filterings
        # come too close in time. What a piece of shit!
        if keyword?
            @user_filters['keyword'] = keyword
        else
            delete @user_filters['keyword']
        
        if type?
            @type_filter = (t for t of type when t)
        else
            @type_filter = []
        
        @highlight_range = {}
        if date? and date.from?
            @highlight_range.from = moment(date.from, "YYYY-MM-DD").toDate().getTime() / 1000
        if date? and date.to?
            @highlight_range.to = moment(date.to, "YYYY-MM-DD").add(1, 'day').toDate().getTime() / 1000
        
        # We really need a full reset only when keywords change,
        # but the query will be probably cached any way,
        # so it probably doesn't really matter much.
        @reset()

    
    reset: ->
        @_reset_pending = true
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
        end_time = new Date(year, month+1, day)
        @time_range =
            start: start_time
            end: end_time
        end_time_str = end_time.getFullYear() + "-" + \
                       (end_time.getMonth()+1) + "-" + \
                       end_time.getDate()

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
            @_reset_pending = false

    draw_plot: ->
        if @plot_series.length == 0
            return
        
        flot2rickshaw = ([x, y]) -> x: x/1000.0, y: y

        st = @time_range.start.getTime()/1000
        et = @time_range.end.getTime()/1000
        # Hackidi hack to force the data domain.
        data = [x: st, y: null]
        data.push @plot_series[0].data.map(flot2rickshaw)...
        data.push x: et, y: null
        @member_series.data = data
        
        if avg = @plot_series[1]
            conv = avg.data.map flot2rickshaw
            for c in conv
                c.x += SECS_IN_MONTH/2.0 # Point to mid month
            
            data = [x: st, y: null]
            for v, i in conv
                data.push v
                # If we don't have a data for the next month,
                # hack zeros to "flesh out" the values
                continue if not (next = conv[i+1])
                if next.x - v.x > SECS_IN_MONTH*1.5
                    data.push x: v.x+SECS_IN_MONTH, y: 0
                    data.push x: next.x-SECS_IN_MONTH, y: 0
            
            data.push x: et, y: null
            @avg_series.data = data
            @avg_series.disabled = false
        else
            # So many corner cases :(
            @avg_series.data = [
                {x: st, y: null},
                {x: et, y: null}
            ]
            @avg_series.disabled = true
        @graph.renderer.domain()
        @graph.update()

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

                if act.time != time
                    break

                if @type_filter and @type_filter.length
                    if act.type not in @type_filter
                        data_idx += 1
                        continue

                score += act.score
                data_idx += 1
            
            # Hack the bar to be almost centered
            time = new Date(time).getTime()
            
            column = [time, score]
            act_histogram.push column

            max_score = Math.max max_score, score

            data_idx += 1

        return [act_histogram, max_score]

    render: ->
        [act_histogram, max_score] = @get_histogram @collection.models

        if @avg_act_collection
            [avg_histogram, avg_max_score] = @get_histogram @avg_act_collection.models
            draw_avg = true
        else
            draw_avg = false

        @plot_series = []
        @plot_series.push
            data: act_histogram

        if draw_avg
            @plot_series.push
                data: avg_histogram

        @draw_plot()

        return @

###
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
                clickable: true
        }
###
