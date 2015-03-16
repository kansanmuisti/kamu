SECS_IN_MONTH = 86400 * 27

Date.prototype._nextMonth = ->
    new Date @.getFullYear(), @.getMonth()+1, 1

dateToEpoch = (d) ->
    d.getTime()/1000.0
getMonths = (from, to) ->
    res = [from]
    while from <= to
        res.push from = from._nextMonth()
    res

zerofiller = (xrng) -> (items) ->
    for x, i in xrng
        y = 0
        ix = items[0]?[0]
        if ix <= x and not (ix >= xrng[i+1])
            y = items[0][1]
            items = items[1..]
        [x, y]
            

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
        
        dummy_data = []
        @member_series =
            color: "rgba(0, 192, 192, 1.0)"
            name: "Activity"
            data: dummy_data.slice()
            stack: false
            renderer: "stack"
            interpolation: "step-after"

        @avg_series =
            color: "rgba(0, 0, 0, 0.3)"
            name: "Average activity"
            data: dummy_data.slice()
            stack: false
            renderer: "line"
            interpolation: "step-after"
        
        @graph = new Rickshaw.Graph
            width: $el.width()
            height: $el.height()
            element: $el[0]
            renderer: "multi"
            interpolation: "step-after"
            stack: false
            series: [@member_series, @avg_series]
        $(window).resize =>
            # Come on! Do scalable by default
            # people!
            @graph.configure
                width: $el.width()
                height: $el.height()
            @graph.update()
        
        xaxis = new Rickshaw.Graph.Axis.Time graph: @graph
        

        @graph.render()
        xaxis.render()
        
        canvas = $ @graph.vis[0][0]
        $(@graph.vis[0][0]).click (e) =>
            # Come on world! This is sort of basic stuff!
            px = e.offsetX ? (e.clientX - $(canvas).offset().left)
            x = @graph.x.invert px
            #if x > @highlight_range.from and x < @highlight_range.to
            #    @el.trigger "plotdaterange", undefined
            #    return
            # Round to nearest month. For some
            # reason won't work with moment.js
            from = new Date x*1000
            from.setDate 1
            to = new Date from.getFullYear(), from.getMonth()+1, 0
            if to <= @time_range.end
                to = moment(to).format "YYYY-MM-DD"
            else
                to = undefined
            @el.trigger "plotdaterange",
                #from: moment(from).format "YYYY-MM-DD"
                from: undefined
                to: to
        
        @graph.onUpdate =>
            # Hopefully everything is removed already
            el = $ @graph.vis[0][0]
            {from, to} = @highlight_range
            from ?= dateToEpoch @time_range.start
            to ?= dateToEpoch @time_range.end
            #return if not from? and not to?
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
            .attr 'y', 0
            .attr 'height', "100%"
            .attr 'stroke', 'black'
            .attr 'stroke-opacity', 0.3
            .attr 'stroke-width', 2
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
        
        filler = zerofiller getMonths @time_range.start, @time_range.end
        mangle = (data) ->
            for [x, y] in filler(data)
                x: dateToEpoch(x), y: y
        @member_series.data = mangle @plot_series[0].data
        
        if avg = @plot_series[1]
            @avg_series.data = mangle avg.data
            @avg_series.disabled = false
        else
            # So many corner cases :(
            @avg_series.data = [
                {x: @time_range.start, y: null},
                {x: @time_range.end, y: null}
            ]
            @avg_series.disabled = true
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
            
            time = new Date(time)
            
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

