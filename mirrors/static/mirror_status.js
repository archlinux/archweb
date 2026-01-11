function draw_graphs(location_url, log_url, container_id) {
    jQuery.when(jQuery.getJSON(location_url), jQuery.getJSON(log_url))
        .then(function(loc_data, log_data) {
            /* use the same color selection for a given URL in every graph */
            var color = d3.scale.category10();

            for (const [_key, value] of Object.entries(loc_data[0].locations)) {
                mirror_status(container_id, value, log_data[0], color);
            }
        });
}

function mirror_status(container_id, check_loc, log_data, color) {

    var draw_graph = function(chart_id, data) {
        const div = document.querySelector(chart_id);
        const margin = {top: 20, right: 20, bottom: 30, left: 40};
        const rects = div.getBoundingClientRect();
        const width = rects.width - margin.left - margin.right;
        const height = rects.height - margin.top - margin.bottom;

        const x = d3.time.scale.utc().range([0, width]);
        const y = d3.scale.linear().range([height, 0]);
        const x_axis = d3.svg.axis().scale(x).orient("bottom");
        const y_axis = d3.svg.axis().scale(y).orient("left");

        /* remove any existing graph first if we are redrawing after resize */
        d3.select(chart_id).select("svg").remove();
        const svg = d3.select(chart_id).append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        x.domain([
                d3.min(data, function(c) { return d3.min(c.logs, function(v) { return v.check_time; }); }),
                d3.max(data, function(c) { return d3.max(c.logs, function(v) { return v.check_time; }); })
        ]).nice(d3.time.hour);
        y.domain([
                0,
                d3.max(data, function(c) { return d3.max(c.logs, function(v) { return v.duration; }); })
        ]).nice();

        /* build the axis lines... */
        svg.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + height + ")")
            .call(x_axis)
            .append("text")
            .attr("class", "label")
            .attr("x", width)
            .attr("y", -6)
            .style("text-anchor", "end")
            .text("Check Time (UTC)");

        svg.append("g")
            .attr("class", "y axis")
            .call(y_axis)
            .append("text")
            .attr("class", "label")
            .attr("transform", "rotate(-90)")
            .attr("y", 6)
            .attr("dy", ".71em")
            .style("text-anchor", "end")
            .text("Duration (seconds)");

        const line = d3.svg.line()
            .interpolate("basis")
            .x(function(d) { return x(d.check_time); })
            .y(function(d) { return y(d.duration); });

        /* ...then the points and lines between them. */
        const urls = svg.selectAll(".url")
            .data(data)
            .enter()
            .append("g")
            .attr("class", "url");

        urls.append("path")
            .attr("class", "url-line")
            .attr("d", function(d) { return line(d.logs); })
            .style("stroke", function(d) { return color(d.url); });

        urls.selectAll("circle")
            .data(u => u.logs.map(l => { return { url: u.url, check_time: l.check_time, duration: l.duration }; }))
            .enter()
            .append("circle")
            .attr("class", "url-dot")
            .attr("r", 3.5)
            .attr("cx", function(d) { return x(d.check_time); })
            .attr("cy", function(d) { return y(d.duration); })
            .style("fill", function(d) { return color(d.url); })
            .append("title")
            .text(function(d) { return d.url + "\n" + d.duration.toFixed(3) + " secs\n" + d.check_time.toUTCString(); });

        /* add a legend for good measure */
        const active = data.map(item => item.url);
        const legend = svg.selectAll(".legend")
            .data(active)
            .enter().append("g")
            .attr("class", "legend")
            .attr("transform", function(d, i) { return "translate(0," + i * 20 + ")"; });

        legend.append("rect")
            .attr("x", width - 18)
            .attr("width", 18)
            .attr("height", 18)
            .style("fill", color);

        legend.append("text")
            .attr("x", width - 24)
            .attr("y", 9)
            .attr("dy", ".35em")
            .style("text-anchor", "end")
            .text(function(d) { return d; });
    };

    const filter_data = function(json, location_id) {
        const data = [];
        for (const url of json.urls) {
            const logs = [];
            for (const log of url.logs) {
                if (!log.is_success)
                  continue;

                /* screen by location ID if we were given one */
                if (location_id && log.location_id !== location_id) {
                    continue;
                }

                logs.push({
                    duration: log.duration,
                    check_time: new Date(log.check_time)
                });
            };

            if (logs.length === 0)
                continue;

            data.push({
                url: url.url,
                logs: logs
            });
        }

        return data;
    };

    const cached_data = filter_data(log_data, check_loc.id);
    /* we had a check location with no log data handed to us, skip graphing */
    if (cached_data.length === 0) {
        return;
    }

    /* create the containers, defer the actual graph drawing */
    const chart_id = 'status-chart-' + check_loc.id;
    jQuery(container_id).append('<h3><span class="fam-flag fam-flag-' + check_loc.country_code.toLowerCase() + '" title="' + check_loc.country + '"></span> ' + check_loc.country + ' (' + check_loc.source_ip + '), IPv' + check_loc.ip_version + '</h3>');
    jQuery(container_id).append('<div id="' + chart_id + '" class="visualize-mirror visualize-chart"></div>');
    jQuery(container_id).append('<br/>');
    setTimeout(function() {
        draw_graph('#' + chart_id, cached_data);
    }, 0);

    /* then hook up a resize handler to redraw if necessary */
    var resize_timeout = null;
    const real_resize = function() {
        resize_timeout = null;
        draw_graph('#' + chart_id, cached_data);
    };
    window.addEventListener('resize', function() {
        if (resize_timeout) {
            clearTimeout(resize_timeout);
        }
        resize_timeout = setTimeout(real_resize, 200);
    });
}
