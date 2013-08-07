`var smooth = function (list, degree) {
    var win = degree*2-1;
    weight = _.range(0, win).map(function (x) { return 1.0; });
    weightGauss = [];
    for (i in _.range(0, win)) {
        i = i-degree+1;
        frac = i/win;
        gauss = 1 / Math.exp((4*(frac))*(4*(frac)));
        weightGauss.push(gauss);
    }
    weight = _(weightGauss).zip(weight).map(function (x) { return x[0]*x[1]; });
    smoothed = _.range(0, (list.length+1)-win).map(function (x) { return 0.0; });
    for (i=0; i < smoothed.length; i++) {
        smoothed[i] = _(list.slice(i, i+win)).zip(weight).map(function (x) { return x[0]*x[1]; }).reduce(function (memo, num){ return memo + num; }, 0) / _(weight).reduce(function (memo, num){ return memo + num; }, 0);
    }
    return smoothed;
}`

default_multires_smoother = (data,
        unitscale=60*60*24*1000, # Seconds in a day
        smoothingscale=30,
        minlevel=1,
        maxlevel=30
        levelstep=1
        binlevel=1
        splinelevel=10
        ) ->
    # Don't mangle the argument
    # TODO: Assumes grid-x
    datac = []
    for v in data
        vc = {}
        for vk, vv of v
            vc[vk] = vv
        vc.orig_y = vc.y
        vc.orig_x = vc.x
        vc.cache = {}
        datac.push vc

    getter = (range) ->
        level = (range[1] - range[0])/unitscale/smoothingscale
        level = Math.round(level/levelstep)*levelstep
        level = Math.min(level, maxlevel)
        level = Math.max(level, minlevel)
        if level <= binlevel
            level = 1
        
        # TODO: There are a lot faster methods!
        x = datac[0].orig_x
        for i in [0...x.length]
            break if x[i] >= range[0]
        start = Math.max 0, i-1
        for i in [i...x.length]
            break if x[i] > range[1]
        end = i+1

        for h in datac
            # TODO! Handle the boundaries properly!
            if level not of h.cache
                if level <= 1
                    h.cache[level] = h.orig_y
                else
                    # TODO Downsample
                    h.cache[level] = smooth(h.orig_y, level)
            h.y = h.cache[level][start...end]
            h.x = h.orig_x[start...end][...h.y.length]
        
        opts = {}
        opts.interpolate = switch
            when level <= binlevel then "step"
            when level <= splinelevel then "basis"
            else "linear"
        
        promise = $.Deferred()
        promise.resolve datac, opts
        return promise

    getter.extent = d3.extent datac[0].x
    getter.keys = (d.key for d in datac)
    return getter

#class @MultiresBarChart
#    constructor: (el, @res_data

class @MultiresStackedGraph
    constructor: (el, @res_data) ->
        if not (@res_data instanceof Function)
            @res_data = default_multires_smoother res_data
        
        @$el = $(el)
        
        @contextheight = 41
        @axismargin = 25
        @margin =
            top: 0
            bottom: @axismargin+@contextheight+@axismargin
            left: 30
            right: 0
        @margin.x = @margin.left + @margin.right
        @margin.y = @margin.top + @margin.bottom

        @root = d3.select(el).append("svg")
        .attr("class", "axisplot")
        
        getx = =>
            d3.time.scale()
            .domain(@res_data.extent)
        gety = => d3.scale.linear()

        @x = x = getx()
            
        @y = y = gety()
        
        @area = d3.svg.area()
            .x(([d, i]) -> x d.x[i])
            .y0(([d, i]) -> y d.y0[i])
            .y1(([d, i]) -> y (d.y0[i] + d.y[i]))
        
        @zoom = d3.behavior.zoom()
        
        color = d3.scale.category20()
        .domain(@res_data.keys)
    
        @plot = @root.append("g")
        .attr("transform", "translate(#{@margin.left}, #{@margin.top})")
        
        @xAxis = d3.svg.axis()
        .scale(x)
        .orient("bottom")
        .ticks(5)

        @xAxisEl = @plot.append("g")
        .attr("class", "x axis")
        
        @yAxis = d3.svg.axis()
        .scale(y)
        .orient("left")
        .ticks(4)
        @plot.append("g")
        .attr("class", "y axis")

        @plot.append("clipPath")
        .attr("id", "plotclip")
        .append("use")
        .attr("xlink:href", "#plotrect")
        
               
        areas = @plot.selectAll(".group")
        .data(@res_data.keys)
        .enter().append('g')
        .attr("class", "group")
        .attr("style", "clip-path: url(#plotclip);")
        
        @paths = areas.append("path")
        .attr("class", "area")
        .style("fill", (d) -> color(d))
        
        # NOTE: The rect has to after the plots
        # so that it has a higher "z-index" and gets
        # all mouse events.
        @plotrect = @plot.append("rect")
        .attr("id", "plotrect")
        .attr("class", "pane")
        
        @zoom.on("zoom", @_draw)
        
        $(window).on "resize", =>
            @_render_base()
            @_draw()

        @context = @root.append("g")
        @contextX = getx()
        @contextY = gety()
        @contextXAxis = d3.svg.axis()
        .scale(@contextX)
        .orient("bottom")
        .ticks(6)
        @contextXAxisEl = @context.append("g")
        .attr("class", "x axis")
        
        @contextPath = @context.append("path")
        .attr("class", "area")
        .style("fill", "gray")

        @brush = d3.svg.brush()
        .x(@contextX)
        .on("brush", @_draw)

        @brushEl = @context.append("g")
        .attr("class", "x brush")
        
        @contextArea = d3.svg.area()
        .x(([d, i]) => @contextX d.x[i])
        .y0(@contextheight)
        .y1(([d, i]) => @contextY(d.y0[i] + d.y[i]))
        
                
        @res_data(@res_data.extent).done (data) =>
            @_stack(data)
            last = data[data.length-1]
            d_and_i = (d) -> ([d, i] for i in [0...d.x.length])
            lasty = (last.y[i] + last.y0[i] for i in [0...last.y0.length])
            last = d_and_i last
            @contextY.domain([0, d3.max lasty])
            @contextPath.datum(last)
            
            # We need to first set up the brush..
            @brushEl.call(@brush)
            # Then set up the "canvas"
            @_render_base()

            # Set the extent
            lastx = @res_data.extent[1]
            @brush.extent([new Date(lastx-(60*60*60*24*1000)), lastx])
            # And then call it again, to show the initial brush area
            @brushEl.call(@brush)
            @_draw()

    _render_base: =>
        elwidth = @$el.width()
        elheight = @$el.height()
    
        @root
        .attr("width", elwidth)
        .attr("height", elheight)

        width = elwidth - @margin.x
        height = elheight - @margin.y
        
        @x.range([0, width])
        # TODO: The axis seems to steal 4 pixels!
        @y.range([height, 0])

                
        @xAxisEl
        .attr("transform", "translate(0, #{height})")
       
                
        @plotrect
        .attr("width", width)
        .attr("height", height)

        @zoom.x(@x)
        @plotrect.call(@zoom)
        
        @contextX.range([0, width])
        @contextY.range([@contextheight, 0])

        @context
        .attr("height", @contextheight)
        .attr("transform", "translate(#{@margin.left}, #{height+@axismargin})")
        @contextXAxisEl
        .attr("transform", "translate(0, #{@contextheight})")
        .call(@contextXAxis)
        
        @brushEl.selectAll('rect')
        .attr('height', @contextheight)
        
        @brushEl.select('.background')
        .attr('width', width)

        @contextPath
        .attr('d', @contextArea)

    _draw: =>
        @x.domain @brush.extent()
        @res_data(@x.domain())
        .done @_do_draw
    
    _stack: (data) ->
        d.y0 = [] for d in data
        for ix in [0...data[0].y.length]
            y0 = 0
            for d in data
                d.y0.push y0
                y0 += d.y[ix]


    _do_draw: (data, opts) =>
        opts ?= {}
        @area.interpolate opts.interpolate ? "linear"
        
        @_stack(data)
            
        last = data[data.length-1]
        lasty = (last.y[i] + last.y0[i] for i in [0...last.y0.length])
        @y.domain [0, d3.max lasty]
        
        d_and_i = (d) -> ([d, i] for i in [0...d.x.length])
        
        @paths.data(data)
        .attr("d", (d) => @area d_and_i d)

        # TODO: Limit the extent somehow!
        #plot.selectAll(".group .area").attr("d", (d) -> area d_and_i d)
        @plot.select(".axis.x").call(@xAxis)
        #plot.select(".axis.y").call(yAxis)

